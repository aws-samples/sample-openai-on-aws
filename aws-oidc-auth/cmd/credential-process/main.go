package main

import (
	"bufio"
	"context"
	"encoding/json"
	"errors"
	"flag"
	"fmt"
	"net"
	"os"
	"strings"
	"time"

	"golang.org/x/term"

	"aws-oidc-auth/internal/azure"
	"aws-oidc-auth/internal/config"
	"aws-oidc-auth/internal/federation"
	"aws-oidc-auth/internal/jwt"
	"aws-oidc-auth/internal/oidc"
	"aws-oidc-auth/internal/portlock"
	"aws-oidc-auth/internal/provider"
	"aws-oidc-auth/internal/sso"
	"aws-oidc-auth/internal/storage"
	"aws-oidc-auth/internal/version"
)

const credExpiryBufferSecs = 300 // refresh 5 min before actual expiry

var (
	defaultRedirectPort          = 5115
	oidcPortWaitTimeout          = 60 * time.Second
	oidcAuthenticateWithOpts     = oidc.AuthenticateWithOpts
	oidcRefreshTokenExchangeOpts = oidc.RefreshTokenExchangeWithOpts
	assumeRoleWithWebIdentity    = federation.AssumeRoleWithWebIdentity
	getCredentialsViaCognito     = federation.GetCredentialsViaCognito
	debugMode                    = os.Getenv("AWS_OIDC_AUTH_DEBUG") == "1"
)

func debugf(format string, args ...interface{}) {
	if debugMode {
		fmt.Fprintf(os.Stderr, "[debug] "+format+"\n", args...)
	}
}

func main() {
	os.Exit(run())
}

func run() int {
	profileFlag := flag.String("profile", "", "config.json profile name (auto-detected if only one profile)")
	versionFlag := flag.Bool("version", false, "print version and exit")
	checkExpirationFlag := flag.Bool("check-expiration", false, "print credential expiration status and exit")
	refreshIfNeededFlag := flag.Bool("refresh-if-needed", false, "refresh credentials only if expired or near expiry")
	clearCacheFlag := flag.Bool("clear-cache", false, "clear cached credentials and force re-authentication")
	setClientSecretFlag := flag.Bool("set-client-secret", false, "store Azure AD client secret in OS keyring")
	getMonitoringTokenFlag := flag.Bool("get-monitoring-token", false, "print the cached OIDC monitoring token (used by otel-helper) and exit")
	flag.Parse()

	if *versionFlag {
		fmt.Fprintf(os.Stderr, "aws-oidc-auth credential-process %s\n", version.Version)
		return 0
	}

	profileName := *profileFlag
	if profileName == "" {
		profileName = os.Getenv("AWS_OIDC_AUTH_PROFILE")
	}
	if profileName == "" {
		profileName = os.Getenv("AWS_PROFILE")
	}
	if profileName == "" {
		profileName = config.AutoDetectProfile()
	}
	if profileName == "" {
		fmt.Fprintln(os.Stderr, "error: profile name required (use --profile, AWS_OIDC_AUTH_PROFILE, or AWS_PROFILE, or have exactly one profile in config.json)")
		return 1
	}

	cfg, err := config.LoadProfile(profileName)
	if err != nil {
		fmt.Fprintf(os.Stderr, "error loading profile %q: %v\n", profileName, err)
		return 1
	}

	// Inject Azure client secret from env or keyring into config
	if cfg.ProviderType == "azure" || cfg.AzureAuthMode != "" {
		if envSecret := os.Getenv("AWS_OIDC_AUTH_CLIENT_SECRET"); envSecret != "" {
			cfg.ClientSecret = envSecret
		} else if cfg.AzureAuthMode == "" || cfg.AzureAuthMode == "secret" {
			if secret, err := azure.ReadClientSecret(profileName); err == nil && secret != "" {
				cfg.ClientSecret = secret
			}
		}
	}

	debugf("profile=%s federation=%s provider=%s storage=%s", profileName, cfg.FederationType, cfg.ProviderType, cfg.CredentialStorage)

	// Utility flags
	if *setClientSecretFlag {
		return runSetClientSecret(profileName)
	}
	if *clearCacheFlag {
		return runClearCache(profileName, cfg.CredentialStorage)
	}
	if *checkExpirationFlag {
		return runCheckExpiration(profileName, cfg.CredentialStorage)
	}
	if *getMonitoringTokenFlag {
		return runGetMonitoringToken(profileName, cfg)
	}
	if *refreshIfNeededFlag {
		return runRefreshIfNeeded(profileName, cfg)
	}

	// Normal credential_process flow
	return runCredentialProcess(profileName, cfg)
}

func runCredentialProcess(profile string, cfg *config.ProfileConfig) int {
	// Try cached credentials first
	creds, remaining, err := readUsableCachedCredentials(profile, cfg.CredentialStorage, float64(credExpiryBufferSecs))
	if err == nil && creds != nil {
		debugf("cached credentials found, %.0fs remaining", remaining)
		return outputCredentials(creds)
	}
	if err == nil && remaining > 0 {
		debugf("credentials expiring soon, refreshing")
	}

	return authenticate(profile, cfg)
}

func runRefreshIfNeeded(profile string, cfg *config.ProfileConfig) int {
	creds, remaining, err := readUsableCachedCredentials(profile, cfg.CredentialStorage, float64(credExpiryBufferSecs))
	if err == nil && creds != nil {
		debugf("credentials still valid (%.0fs remaining), no refresh needed", remaining)
		return 0
	}
	return authenticate(profile, cfg)
}

func runCheckExpiration(profile string, credentialStorage string) int {
	creds, err := readCachedCredentials(profile, credentialStorage)
	if err != nil {
		fmt.Fprintf(os.Stderr, "no cached credentials: %v\n", err)
		return 1
	}
	if creds == nil || storage.IsExpiredDummy(creds) {
		fmt.Fprintln(os.Stderr, "no valid credentials cached")
		return 1
	}
	remaining := storage.ParseExpirationSeconds(creds.Expiration)
	if remaining <= 0 {
		fmt.Fprintf(os.Stderr, "credentials expired\n")
		return 1
	}
	fmt.Fprintf(os.Stderr, "credentials valid, expires in %.0f seconds (%s)\n", remaining, creds.Expiration)
	return 0
}

// runGetMonitoringToken prints the cached OIDC monitoring token to stdout for
// otel-helper to consume. It is the counterpart of the --get-monitoring-token
// flag otel-helper invokes; without it, otel-helper falls back to empty
// attribution headers on every cold start.
func runGetMonitoringToken(profile string, cfg *config.ProfileConfig) int {
	token, err := storage.GetMonitoringToken(profile, cfg.CredentialStorage)
	if err != nil || token == "" {
		debugf("no monitoring token available: %v", err)
		return 1
	}
	fmt.Fprintln(os.Stdout, token)
	return 0
}

func runClearCache(profile string, credentialStorage string) int {
	if credentialStorage == "keyring" {
		if err := storage.ClearKeyring(profile); err != nil {
			fmt.Fprintf(os.Stderr, "error clearing keyring: %v\n", err)
			return 1
		}
	} else {
		expired := &federation.AWSCredentials{
			Version:         1,
			AccessKeyID:     "EXPIRED",
			SecretAccessKey: "EXPIRED",
			SessionToken:    "EXPIRED",
			Expiration:      "2000-01-01T00:00:00Z",
		}
		if err := storage.SaveToCredentialsFile(expired, profile); err != nil {
			fmt.Fprintf(os.Stderr, "error clearing session file: %v\n", err)
			return 1
		}
	}
	if err := storage.ClearMonitoringToken(profile, credentialStorage); err != nil {
		fmt.Fprintf(os.Stderr, "warning: failed to clear monitoring token: %v\n", err)
	}
	if err := storage.ClearRefreshToken(profile, credentialStorage); err != nil {
		fmt.Fprintf(os.Stderr, "warning: failed to clear refresh token: %v\n", err)
	}
	fmt.Fprintln(os.Stderr, "credentials cleared")
	return 0
}

func runSetClientSecret(profile string) int {
	fmt.Fprint(os.Stderr, "Enter Azure AD client secret: ")
	var secret string
	var err error

	if term.IsTerminal(int(os.Stdin.Fd())) {
		var b []byte
		b, err = term.ReadPassword(int(os.Stdin.Fd()))
		secret = string(b)
		fmt.Fprintln(os.Stderr) // newline after hidden input
	} else {
		scanner := bufio.NewScanner(os.Stdin)
		if scanner.Scan() {
			secret = strings.TrimRight(scanner.Text(), "\r\n")
		}
		err = scanner.Err()
	}
	if err != nil {
		fmt.Fprintf(os.Stderr, "error reading secret: %v\n", err)
		return 1
	}
	if secret == "" {
		fmt.Fprintln(os.Stderr, "error: secret cannot be empty")
		return 1
	}

	if err := azure.SaveClientSecret(profile, secret); err != nil {
		fmt.Fprintf(os.Stderr, "error saving secret: %v\n", err)
		return 1
	}
	fmt.Fprintln(os.Stderr, "client secret saved to keyring")
	return 0
}

func authenticate(profile string, cfg *config.ProfileConfig) int {
	switch cfg.FederationType {
	case "sso":
		return runSSO(profile, cfg)
	default:
		return runOIDC(profile, cfg)
	}
}

// runSSO handles AWS IAM Identity Center (SSO) federation.
func runSSO(profile string, cfg *config.ProfileConfig) int {
	ctx, cancel := context.WithTimeout(context.Background(), 10*time.Minute)
	defer cancel()

	cachedToken, err := sso.ReadCachedToken(cfg.SSOStartURL)
	if err != nil || !sso.IsTokenValid(cachedToken) {
		debugf("SSO token missing or expired, starting device auth flow")
		cachedToken, err = sso.RunDeviceAuthFlow(ctx, cfg.SSOStartURL, cfg.SSORegion)
		if err != nil {
			fmt.Fprintf(os.Stderr, "SSO login failed: %v\n", err)
			return 1
		}
	} else {
		debugf("using cached SSO token")
	}

	creds, err := sso.GetRoleCredentials(ctx, cfg.SSORegion, cachedToken.AccessToken, cfg.SSOAccountID, cfg.SSORoleName)
	if err != nil {
		fmt.Fprintf(os.Stderr, "getting SSO role credentials: %v\n", err)
		return 1
	}

	if err := saveCachedCredentials(creds, profile, cfg.CredentialStorage); err != nil {
		fmt.Fprintf(os.Stderr, "warning: failed to cache credentials: %v\n", err)
	}

	return outputCredentials(creds)
}

// runOIDC handles OIDC-based federation (direct STS or Cognito).
func runOIDC(profile string, cfg *config.ProfileConfig) int {
	providerType, err := resolveProviderType(cfg)
	if err != nil {
		fmt.Fprintf(os.Stderr, "error: %v\n", err)
		return 1
	}

	// Acquire redirect port — wait if another instance is mid-auth
	ln, creds, err := acquireRedirectPort(profile, cfg.CredentialStorage)
	if err != nil {
		fmt.Fprintf(os.Stderr, "error acquiring port %d: %v\n", defaultRedirectPort, err)
		return 1
	}
	if creds != nil {
		return outputCredentials(creds)
	}
	ln.Close()

	creds, _, err = readUsableCachedCredentials(profile, cfg.CredentialStorage, float64(credExpiryBufferSecs))
	if err == nil && creds != nil {
		return outputCredentials(creds)
	}

	if creds, err := trySilentRefresh(profile, cfg, providerType); err != nil {
		debugf("silent refresh failed: %v", err)
	} else if creds != nil {
		return outputCredentials(creds)
	}

	if creds, err := tryRefreshToken(profile, cfg, providerType); err != nil {
		debugf("refresh token renewal failed: %v", err)
	} else if creds != nil {
		return outputCredentials(creds)
	}

	// Build auth options
	confidentialClient, err := buildConfidentialClient(cfg, providerType)
	if err != nil {
		fmt.Fprintf(os.Stderr, "error: %v\n", err)
		return 1
	}
	authOpts := &oidc.AuthOptions{
		ProviderDomain:     cfg.ProviderDomain,
		ClientID:           cfg.ClientID,
		ProviderType:       providerType,
		RedirectPort:       defaultRedirectPort,
		ConfidentialClient: confidentialClient,
	}

	result, err := oidcAuthenticateWithOpts(authOpts)
	if err != nil {
		fmt.Fprintf(os.Stderr, "authentication failed: %v\n", err)
		return 1
	}
	debugf("OIDC authentication successful")

	// Save monitoring token for otel-helper
	if err := storage.SaveMonitoringToken(profile, cfg.CredentialStorage, result.IDToken, result.TokenClaims); err != nil {
		fmt.Fprintf(os.Stderr, "warning: failed to save monitoring token: %v\n", err)
	}

	// Exchange OIDC token for AWS credentials
	creds, err = getAWSCredentials(cfg, providerType, result)
	if err != nil {
		fmt.Fprintf(os.Stderr, "credential exchange failed: %v\n", err)
		return 1
	}
	debugf("credential exchange successful, expires %s", creds.Expiration)

	if err := saveCachedCredentials(creds, profile, cfg.CredentialStorage); err != nil {
		fmt.Fprintf(os.Stderr, "warning: failed to cache credentials: %v\n", err)
	}
	if err := storage.SaveRefreshToken(profile, cfg.CredentialStorage, result.RefreshToken); err != nil {
		fmt.Fprintf(os.Stderr, "warning: failed to save refresh token: %v\n", err)
	}

	return outputCredentials(creds)
}

func resolveProviderType(cfg *config.ProfileConfig) (string, error) {
	if cfg.ProviderType == "" || cfg.ProviderType == "auto" {
		detected := provider.Detect(cfg.ProviderDomain)
		if provider.IsKnown(detected) {
			return detected, nil
		}
		return "", fmt.Errorf(
			"could not auto-detect provider type for domain %q; set provider_type to one of okta, auth0, azure, or cognito",
			cfg.ProviderDomain,
		)
	}
	if !provider.IsKnown(cfg.ProviderType) {
		return "", fmt.Errorf(
			"unsupported provider_type %q; supported values are okta, auth0, azure, cognito, or auto",
			cfg.ProviderType,
		)
	}
	return cfg.ProviderType, nil
}

func buildConfidentialClient(cfg *config.ProfileConfig, providerType string) (*oidc.ConfidentialClientOpts, error) {
	if providerType != "azure" {
		return nil, nil
	}

	switch cfg.AzureAuthMode {
	case "", "public":
		return nil, nil
	case "certificate":
		tokenURL, err := buildTokenURL(cfg.ProviderDomain, providerType)
		if err != nil {
			return nil, err
		}
		assertion, err := azure.BuildClientAssertion(
			cfg.ClientCertificatePath,
			cfg.ClientCertificateKeyPath,
			cfg.ClientID,
			tokenURL,
		)
		if err != nil {
			return nil, fmt.Errorf("building client assertion: %w", err)
		}
		return &oidc.ConfidentialClientOpts{
			ClientAssertion:     assertion,
			ClientAssertionType: "urn:ietf:params:oauth:client-assertion-type:jwt-bearer",
		}, nil
	case "secret":
		if cfg.ClientSecret == "" {
			return nil, fmt.Errorf("azure_auth_mode=secret but no client secret found; run with --set-client-secret or set AWS_OIDC_AUTH_CLIENT_SECRET")
		}
		return &oidc.ConfidentialClientOpts{ClientSecret: cfg.ClientSecret}, nil
	default:
		return nil, fmt.Errorf("unsupported azure_auth_mode %q", cfg.AzureAuthMode)
	}
}

func buildTokenURL(providerDomain, providerType string) (string, error) {
	provCfg, ok := provider.Configs[providerType]
	if !ok {
		return "", fmt.Errorf("unknown provider type %q", providerType)
	}

	domain := providerDomain
	if providerType == "azure" && strings.HasSuffix(domain, "/v2.0") {
		domain = strings.TrimSuffix(domain, "/v2.0")
	}

	return "https://" + domain + provCfg.TokenEndpoint, nil
}

func acquireRedirectPort(profile, storageType string) (net.Listener, *federation.AWSCredentials, error) {
	for {
		ln, err := portlock.TryAcquire(defaultRedirectPort)
		if err != nil {
			return nil, nil, err
		}
		if ln != nil {
			return ln, nil, nil
		}

		debugf("port %d busy, waiting for it to free", defaultRedirectPort)
		if !portlock.WaitForRelease(defaultRedirectPort, oidcPortWaitTimeout) {
			return nil, nil, fmt.Errorf("timeout waiting for port %d to become available", defaultRedirectPort)
		}

		creds, _, err := readUsableCachedCredentials(profile, storageType, float64(credExpiryBufferSecs))
		if err == nil && creds != nil {
			return nil, creds, nil
		}
		if err != nil {
			debugf("checking cached credentials after port wait failed: %v", err)
		}
		debugf("port %d released without cached credentials, retrying auth flow", defaultRedirectPort)
	}
}

func trySilentRefresh(profile string, cfg *config.ProfileConfig, providerType string) (*federation.AWSCredentials, error) {
	token, err := storage.GetMonitoringToken(profile, cfg.CredentialStorage)
	if err != nil || token == "" {
		return nil, nil
	}

	claims, err := jwt.DecodePayload(token)
	if err != nil {
		return nil, fmt.Errorf("decoding cached monitoring token: %w", err)
	}
	if exp := claims.GetFloat("exp"); exp > 0 && int64(exp) < time.Now().Unix() {
		return nil, nil
	}

	creds, err := getAWSCredentials(cfg, providerType, &oidc.AuthResult{
		IDToken:     token,
		TokenClaims: claims,
	})
	if err != nil {
		return nil, err
	}

	if err := saveCachedCredentials(creds, profile, cfg.CredentialStorage); err != nil {
		debugf("failed to cache silently refreshed credentials: %v", err)
	}
	if err := storage.SaveMonitoringToken(profile, cfg.CredentialStorage, token, map[string]interface{}(claims)); err != nil {
		debugf("failed to refresh cached monitoring token: %v", err)
	}
	return creds, nil
}

func tryRefreshToken(profile string, cfg *config.ProfileConfig, providerType string) (*federation.AWSCredentials, error) {
	refreshToken := storage.LoadRefreshToken(profile, cfg.CredentialStorage)
	if refreshToken == "" {
		return nil, nil
	}

	tokenURL, err := buildTokenURL(cfg.ProviderDomain, providerType)
	if err != nil {
		return nil, err
	}
	confidentialClient, err := buildConfidentialClient(cfg, providerType)
	if err != nil {
		return nil, err
	}

	tokenResp, err := oidcRefreshTokenExchangeOpts(tokenURL, refreshToken, cfg.ClientID, confidentialClient)
	if err != nil {
		if shouldClearRefreshToken(err) {
			if clearErr := storage.ClearRefreshToken(profile, cfg.CredentialStorage); clearErr != nil {
				debugf("failed to clear invalid refresh token: %v", clearErr)
			}
		}
		return nil, err
	}
	if tokenResp.IDToken == "" {
		return nil, nil
	}

	claims, err := jwt.DecodePayload(tokenResp.IDToken)
	if err != nil {
		return nil, fmt.Errorf("decoding refreshed ID token: %w", err)
	}

	creds, err := getAWSCredentials(cfg, providerType, &oidc.AuthResult{
		IDToken:      tokenResp.IDToken,
		RefreshToken: tokenResp.RefreshToken,
		TokenClaims:  claims,
	})
	if err != nil {
		return nil, err
	}

	if err := saveCachedCredentials(creds, profile, cfg.CredentialStorage); err != nil {
		debugf("failed to cache refresh-token credentials: %v", err)
	}
	if err := storage.SaveMonitoringToken(profile, cfg.CredentialStorage, tokenResp.IDToken, map[string]interface{}(claims)); err != nil {
		debugf("failed to cache refreshed monitoring token: %v", err)
	}
	if tokenResp.RefreshToken != "" {
		if err := storage.SaveRefreshToken(profile, cfg.CredentialStorage, tokenResp.RefreshToken); err != nil {
			debugf("failed to save rotated refresh token: %v", err)
		}
	}

	return creds, nil
}

func shouldClearRefreshToken(err error) bool {
	var exchangeErr *oidc.TokenExchangeError
	return errors.As(err, &exchangeErr) && exchangeErr.IsInvalidGrant()
}

func getAWSCredentials(cfg *config.ProfileConfig, providerType string, result *oidc.AuthResult) (*federation.AWSCredentials, error) {
	switch cfg.FederationType {
	case "direct":
		return assumeRoleWithWebIdentity(
			cfg.AWSRegion, cfg.FederatedRoleARN, result.IDToken,
			result.TokenClaims, cfg.MaxSessionDuration,
		)
	default:
		return getCredentialsViaCognito(
			cfg.AWSRegion, cfg.IdentityPoolID, cfg.ProviderDomain,
			providerType, result.IDToken, result.TokenClaims,
		)
	}
}

func readCachedCredentials(profile, storageType string) (*federation.AWSCredentials, error) {
	if storageType == "keyring" {
		return storage.ReadFromKeyring(profile)
	}
	return storage.ReadFromCredentialsFile(profile)
}

func readUsableCachedCredentials(profile, storageType string, minRemaining float64) (*federation.AWSCredentials, float64, error) {
	creds, err := readCachedCredentials(profile, storageType)
	if err != nil {
		return nil, 0, err
	}
	if creds == nil || storage.IsExpiredDummy(creds) {
		return nil, 0, nil
	}

	remaining := storage.ParseExpirationSeconds(creds.Expiration)
	if remaining <= minRemaining {
		return nil, remaining, nil
	}

	return creds, remaining, nil
}

func saveCachedCredentials(creds *federation.AWSCredentials, profile, storageType string) error {
	if storageType == "keyring" {
		return storage.SaveToKeyring(creds, profile)
	}
	return storage.SaveToCredentialsFile(creds, profile)
}

func outputCredentials(creds *federation.AWSCredentials) int {
	enc := json.NewEncoder(os.Stdout)
	enc.SetIndent("", "  ")
	if err := enc.Encode(creds); err != nil {
		fmt.Fprintf(os.Stderr, "error encoding credentials: %v\n", err)
		return 1
	}
	return 0
}
