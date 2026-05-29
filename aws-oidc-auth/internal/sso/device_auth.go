package sso

import (
	"context"
	"errors"
	"fmt"
	"os"
	"time"

	"github.com/aws/aws-sdk-go-v2/aws"
	awsconfig "github.com/aws/aws-sdk-go-v2/config"
	"github.com/aws/aws-sdk-go-v2/service/ssooidc"
	"github.com/aws/aws-sdk-go-v2/service/ssooidc/types"

	"aws-oidc-auth/internal/browser"
)

const clientName = "aws-oidc-auth"

func RunDeviceAuthFlow(ctx context.Context, startURL, region string) (*CachedToken, error) {
	cfg, err := awsconfig.LoadDefaultConfig(ctx,
		awsconfig.WithRegion(region),
		awsconfig.WithCredentialsProvider(aws.AnonymousCredentials{}),
	)
	if err != nil {
		return nil, fmt.Errorf("loading AWS config: %w", err)
	}

	client := ssooidc.NewFromConfig(cfg)

	// Register OIDC client
	regOut, err := client.RegisterClient(ctx, &ssooidc.RegisterClientInput{
		ClientName: aws.String(clientName),
		ClientType: aws.String("public"),
	})
	if err != nil {
		return nil, fmt.Errorf("registering client: %w", err)
	}

	// Start device authorization
	authOut, err := client.StartDeviceAuthorization(ctx, &ssooidc.StartDeviceAuthorizationInput{
		ClientId:     regOut.ClientId,
		ClientSecret: regOut.ClientSecret,
		StartUrl:     aws.String(startURL),
	})
	if err != nil {
		return nil, fmt.Errorf("starting device authorization: %w", err)
	}

	// Open browser for user
	verificationURL := aws.ToString(authOut.VerificationUriComplete)
	if verificationURL == "" {
		verificationURL = aws.ToString(authOut.VerificationUri)
	}

	fmt.Fprintf(os.Stderr, "Opening browser for SSO login...\n")
	fmt.Fprintf(os.Stderr, "If browser doesn't open, visit: %s\n", verificationURL)
	if authOut.UserCode != nil {
		fmt.Fprintf(os.Stderr, "Enter code: %s\n", aws.ToString(authOut.UserCode))
	}

	_ = browser.OpenURL(verificationURL)

	// Poll for token
	interval := int32(authOut.Interval)
	if interval < 1 {
		interval = 5
	}

	tokenOut, err := pollForToken(ctx, client, regOut.ClientId, regOut.ClientSecret,
		aws.ToString(authOut.DeviceCode), interval)
	if err != nil {
		return nil, err
	}

	// Build and cache token
	expiresAt := time.Now().Add(time.Duration(tokenOut.ExpiresIn) * time.Second)
	cachedToken := &CachedToken{
		StartURL:    startURL,
		Region:      region,
		AccessToken: aws.ToString(tokenOut.AccessToken),
		ExpiresAt:   expiresAt.UTC().Format("2006-01-02T15:04:05UTC"),
	}

	if regOut.ClientId != nil {
		cachedToken.ClientID = aws.ToString(regOut.ClientId)
	}
	if regOut.ClientSecret != nil {
		cachedToken.ClientSecret = aws.ToString(regOut.ClientSecret)
	}
	if regOut.ClientSecretExpiresAt != 0 {
		regExp := time.Unix(regOut.ClientSecretExpiresAt, 0)
		cachedToken.RegistrationExpiresAt = regExp.UTC().Format("2006-01-02T15:04:05UTC")
	}

	if err := WriteCachedToken(cachedToken); err != nil {
		fmt.Fprintf(os.Stderr, "Warning: failed to cache SSO token: %v\n", err)
	}

	return cachedToken, nil
}

func pollForToken(ctx context.Context, client *ssooidc.Client, clientID, clientSecret *string, deviceCode string, interval int32) (*ssooidc.CreateTokenOutput, error) {
	for {
		select {
		case <-ctx.Done():
			return nil, fmt.Errorf("SSO login timed out")
		default:
		}

		time.Sleep(time.Duration(interval) * time.Second)

		out, err := client.CreateToken(ctx, &ssooidc.CreateTokenInput{
			ClientId:     clientID,
			ClientSecret: clientSecret,
			DeviceCode:   aws.String(deviceCode),
			GrantType:    aws.String("urn:ietf:params:oauth:grant-type:device_code"),
		})
		if err == nil {
			return out, nil
		}

		// Check if we should keep polling
		var authPending *types.AuthorizationPendingException
		var slowDown *types.SlowDownException
		if errors.As(err, &authPending) {
			continue
		}
		if errors.As(err, &slowDown) {
			interval += 5
			continue
		}

		return nil, fmt.Errorf("SSO login failed: %w", err)
	}
}
