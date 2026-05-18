package sso

import (
	"context"
	"fmt"
	"time"

	"github.com/aws/aws-sdk-go-v2/aws"
	awsconfig "github.com/aws/aws-sdk-go-v2/config"
	"github.com/aws/aws-sdk-go-v2/service/sso"

	"aws-oidc-auth/internal/federation"
)

func GetRoleCredentials(ctx context.Context, region, accessToken, accountID, roleName string) (*federation.AWSCredentials, error) {
	cfg, err := awsconfig.LoadDefaultConfig(ctx,
		awsconfig.WithRegion(region),
		awsconfig.WithCredentialsProvider(aws.AnonymousCredentials{}),
	)
	if err != nil {
		return nil, fmt.Errorf("loading AWS config: %w", err)
	}

	client := sso.NewFromConfig(cfg)

	out, err := client.GetRoleCredentials(ctx, &sso.GetRoleCredentialsInput{
		AccountId:   aws.String(accountID),
		RoleName:    aws.String(roleName),
		AccessToken: aws.String(accessToken),
	})
	if err != nil {
		return nil, fmt.Errorf("GetRoleCredentials failed: %w", err)
	}

	creds := out.RoleCredentials
	expiration := time.UnixMilli(creds.Expiration).UTC().Format(time.RFC3339)

	return &federation.AWSCredentials{
		Version:         1,
		AccessKeyID:     aws.ToString(creds.AccessKeyId),
		SecretAccessKey: aws.ToString(creds.SecretAccessKey),
		SessionToken:    aws.ToString(creds.SessionToken),
		Expiration:      expiration,
	}, nil
}
