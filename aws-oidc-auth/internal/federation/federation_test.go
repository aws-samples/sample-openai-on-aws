package federation

import (
	"errors"
	"os"
	"testing"

	"aws-oidc-auth/internal/jwt"
)

func TestBuildSessionName(t *testing.T) {
	tests := []struct {
		name   string
		claims jwt.Claims
		want   string
	}{
		{
			"uses sub",
			jwt.Claims{"sub": "user-abc-123"},
			"oidc-auth-user-abc-123",
		},
		{
			"uses email local-part when no sub",
			jwt.Claims{"email": "alice@example.com"},
			"oidc-auth-alice",
		},
		{
			"sanitizes special chars in sub",
			jwt.Claims{"sub": "user/with:special chars"},
			"oidc-auth-user-with-special-chars",
		},
		{
			// sanitized sub is truncated to 32 chars, then "oidc-auth-" is prepended
			"truncates long sub to 32 chars",
			jwt.Claims{"sub": "abcdefghijklmnopqrstuvwxyz012345extra"},
			"oidc-auth-abcdefghijklmnopqrstuvwxyz012345",
		},
		{
			"falls back to oidc-auth when no sub or email",
			jwt.Claims{},
			"oidc-auth",
		},
	}

	for _, tc := range tests {
		t.Run(tc.name, func(t *testing.T) {
			got := buildSessionName(tc.claims)
			if got != tc.want {
				t.Errorf("got %q, want %q", got, tc.want)
			}
		})
	}
}

func TestIsRetryableAuthError(t *testing.T) {
	retryable := []string{
		"InvalidParameterException",
		"NotAuthorizedException",
		"ValidationError",
		"Invalid AccessKeyId",
		"ExpiredToken",
		"Invalid JWT",
		"Token is not from a supported provider",
	}
	for _, msg := range retryable {
		t.Run(msg, func(t *testing.T) {
			if !IsRetryableAuthError(errors.New("some prefix: " + msg + " suffix")) {
				t.Errorf("expected retryable for %q", msg)
			}
		})
	}

	if IsRetryableAuthError(nil) {
		t.Error("nil error should not be retryable")
	}
	if IsRetryableAuthError(errors.New("random error")) {
		t.Error("unrelated error should not be retryable")
	}
}

func TestDetermineLoginKey_Cognito(t *testing.T) {
	claims := jwt.Claims{"iss": "https://cognito-idp.us-east-1.amazonaws.com/pool-id"}
	got := determineLoginKey("cognito", "fallback.domain", claims)
	want := "cognito-idp.us-east-1.amazonaws.com/pool-id"
	if got != want {
		t.Errorf("got %q, want %q", got, want)
	}
}

func TestDetermineLoginKey_CognitoFallback(t *testing.T) {
	// No iss claim → use providerDomain
	got := determineLoginKey("cognito", "my.pool.domain", jwt.Claims{})
	if got != "my.pool.domain" {
		t.Errorf("got %q", got)
	}
}

func TestDetermineLoginKey_NonCognito(t *testing.T) {
	got := determineLoginKey("okta", "dev-123.okta.com", jwt.Claims{"iss": "https://dev-123.okta.com"})
	if got != "dev-123.okta.com" {
		t.Errorf("got %q", got)
	}
}

func TestTemporaryEnvClear(t *testing.T) {
	t.Setenv("AWS_PROFILE", "test-profile")
	t.Setenv("AWS_ACCESS_KEY_ID", "AKID")

	restore := TemporaryEnvClear()

	if os.Getenv("AWS_PROFILE") != "" {
		t.Error("AWS_PROFILE should be cleared")
	}
	if os.Getenv("AWS_ACCESS_KEY_ID") != "" {
		t.Error("AWS_ACCESS_KEY_ID should be cleared")
	}

	restore()

	if os.Getenv("AWS_PROFILE") != "test-profile" {
		t.Errorf("AWS_PROFILE not restored: got %q", os.Getenv("AWS_PROFILE"))
	}
	if os.Getenv("AWS_ACCESS_KEY_ID") != "AKID" {
		t.Errorf("AWS_ACCESS_KEY_ID not restored: got %q", os.Getenv("AWS_ACCESS_KEY_ID"))
	}
}

func TestClearAndRestoreAWSEnv(t *testing.T) {
	t.Setenv("AWS_SESSION_TOKEN", "session-tok")

	saved := clearAWSEnv()
	if os.Getenv("AWS_SESSION_TOKEN") != "" {
		t.Error("AWS_SESSION_TOKEN should be cleared")
	}

	restoreEnv(saved)
	if os.Getenv("AWS_SESSION_TOKEN") != "session-tok" {
		t.Errorf("AWS_SESSION_TOKEN not restored: got %q", os.Getenv("AWS_SESSION_TOKEN"))
	}
}
