package main

import (
	"encoding/json"
	"flag"
	"os"
	"path/filepath"
	"testing"
	"time"

	"aws-oidc-auth/internal/federation"
	"aws-oidc-auth/internal/storage"
)

// resetFlags resets the global flag.CommandLine between test calls to run(),
// which registers flags on each invocation.
func resetFlags() {
	flag.CommandLine = flag.NewFlagSet(os.Args[0], flag.ContinueOnError)
}

func setupConfig(t *testing.T, tmp, content string) {
	t.Helper()
	dir := filepath.Join(tmp, "aws-oidc-auth")
	if err := os.MkdirAll(dir, 0700); err != nil {
		t.Fatal(err)
	}
	if err := os.WriteFile(filepath.Join(dir, "config.json"), []byte(content), 0600); err != nil {
		t.Fatal(err)
	}
}

func writeCreds(t *testing.T, tmp, profile, expiration string) {
	t.Helper()
	dir := filepath.Join(tmp, ".aws")
	if err := os.MkdirAll(dir, 0700); err != nil {
		t.Fatal(err)
	}
	content := "[" + profile + "]\n" +
		"aws_access_key_id = AKIDTEST\n" +
		"aws_secret_access_key = SECRETTEST\n" +
		"aws_session_token = TOKENTEST\n" +
		"x-expiration = " + expiration + "\n"
	if err := os.WriteFile(filepath.Join(dir, "credentials"), []byte(content), 0600); err != nil {
		t.Fatal(err)
	}
}

const basicConfig = `{
	"profiles": {
		"default": {
			"provider_domain": "dev-123.okta.com",
			"client_id": "test",
			"aws_region": "us-east-1",
			"credential_storage": "session",
			"federation_type": "cognito",
			"identity_pool_id": "us-east-1:pool"
		}
	}
}`

func TestRun_CheckExpiration_Valid(t *testing.T) {
	resetFlags()
	tmp := t.TempDir()
	t.Setenv("HOME", tmp)
	t.Setenv("USERPROFILE", tmp)
	t.Setenv("AWS_PROFILE", "")
	t.Setenv("AWS_OIDC_AUTH_PROFILE", "")

	setupConfig(t, tmp, basicConfig)
	future := time.Now().Add(1 * time.Hour).UTC().Format(time.RFC3339)
	writeCreds(t, tmp, "default", future)

	os.Args = []string{"credential-process", "--profile", "default", "--check-expiration"}
	if code := run(); code != 0 {
		t.Errorf("expected exit 0, got %d", code)
	}
}

func TestRun_CheckExpiration_Expired(t *testing.T) {
	resetFlags()
	tmp := t.TempDir()
	t.Setenv("HOME", tmp)
	t.Setenv("USERPROFILE", tmp)
	t.Setenv("AWS_PROFILE", "")
	t.Setenv("AWS_OIDC_AUTH_PROFILE", "")

	setupConfig(t, tmp, basicConfig)
	writeCreds(t, tmp, "default", "2000-01-01T00:00:00Z")

	os.Args = []string{"credential-process", "--profile", "default", "--check-expiration"}
	if code := run(); code != 1 {
		t.Errorf("expected exit 1 for expired creds, got %d", code)
	}
}

func TestRun_CheckExpiration_NoCredentials(t *testing.T) {
	resetFlags()
	tmp := t.TempDir()
	t.Setenv("HOME", tmp)
	t.Setenv("USERPROFILE", tmp)
	t.Setenv("AWS_PROFILE", "")
	t.Setenv("AWS_OIDC_AUTH_PROFILE", "")

	setupConfig(t, tmp, basicConfig)

	os.Args = []string{"credential-process", "--profile", "default", "--check-expiration"}
	if code := run(); code != 1 {
		t.Errorf("expected exit 1 for missing creds, got %d", code)
	}
}

func TestRun_ClearCache(t *testing.T) {
	resetFlags()
	tmp := t.TempDir()
	t.Setenv("HOME", tmp)
	t.Setenv("USERPROFILE", tmp)
	t.Setenv("AWS_PROFILE", "")
	t.Setenv("AWS_OIDC_AUTH_PROFILE", "")

	setupConfig(t, tmp, basicConfig)
	future := time.Now().Add(1 * time.Hour).UTC().Format(time.RFC3339)
	writeCreds(t, tmp, "default", future)
	if err := storage.SaveMonitoringToken("default", "session", "monitoring-token", map[string]interface{}{
		"exp": float64(time.Now().Add(1 * time.Hour).Unix()),
	}); err != nil {
		t.Fatalf("save monitoring token: %v", err)
	}
	if err := storage.SaveRefreshToken("default", "session", "refresh-token"); err != nil {
		t.Fatalf("save refresh token: %v", err)
	}

	os.Args = []string{"credential-process", "--profile", "default", "--clear-cache"}
	if code := run(); code != 0 {
		t.Errorf("expected exit 0, got %d", code)
	}

	creds, err := storage.ReadFromCredentialsFile("default")
	if err != nil {
		t.Fatalf("read after clear: %v", err)
	}
	if !storage.IsExpiredDummy(creds) {
		t.Errorf("expected EXPIRED placeholder, got %+v", creds)
	}

	token, err := storage.GetMonitoringToken("default", "session")
	if err != nil {
		t.Fatalf("monitoring token after clear: %v", err)
	}
	if token != "" {
		t.Errorf("expected cleared monitoring token, got %q", token)
	}
	if got := storage.LoadRefreshToken("default", "session"); got != "" {
		t.Errorf("expected cleared refresh token, got %q", got)
	}
}

func TestRun_RefreshIfNeeded_StillValid(t *testing.T) {
	resetFlags()
	tmp := t.TempDir()
	t.Setenv("HOME", tmp)
	t.Setenv("USERPROFILE", tmp)
	t.Setenv("AWS_PROFILE", "")
	t.Setenv("AWS_OIDC_AUTH_PROFILE", "")

	setupConfig(t, tmp, basicConfig)
	future := time.Now().Add(1 * time.Hour).UTC().Format(time.RFC3339)
	writeCreds(t, tmp, "default", future)

	os.Args = []string{"credential-process", "--profile", "default", "--refresh-if-needed"}
	if code := run(); code != 0 {
		t.Errorf("expected exit 0 (no refresh needed), got %d", code)
	}
}

func TestRun_NormalMode_ServesFromCache(t *testing.T) {
	resetFlags()
	tmp := t.TempDir()
	t.Setenv("HOME", tmp)
	t.Setenv("USERPROFILE", tmp)
	t.Setenv("AWS_PROFILE", "")
	t.Setenv("AWS_OIDC_AUTH_PROFILE", "")

	setupConfig(t, tmp, basicConfig)
	future := time.Now().Add(1 * time.Hour).UTC().Format(time.RFC3339)
	writeCreds(t, tmp, "default", future)

	r, w, _ := os.Pipe()
	old := os.Stdout
	os.Stdout = w

	os.Args = []string{"credential-process", "--profile", "default"}
	code := run()

	w.Close()
	os.Stdout = old

	if code != 0 {
		t.Fatalf("expected exit 0, got %d", code)
	}

	buf := make([]byte, 4096)
	n, _ := r.Read(buf)
	var creds federation.AWSCredentials
	if err := json.Unmarshal(buf[:n], &creds); err != nil {
		t.Fatalf("output not valid JSON: %v\nraw: %s", err, buf[:n])
	}
	if creds.AccessKeyID != "AKIDTEST" {
		t.Errorf("AccessKeyID: got %q", creds.AccessKeyID)
	}
}

func TestRun_Version(t *testing.T) {
	resetFlags()
	os.Args = []string{"credential-process", "--version"}
	if code := run(); code != 0 {
		t.Errorf("expected exit 0 for --version, got %d", code)
	}
}

func TestRun_MissingProfile(t *testing.T) {
	resetFlags()
	tmp := t.TempDir()
	t.Setenv("HOME", tmp)
	t.Setenv("USERPROFILE", tmp)
	t.Setenv("AWS_PROFILE", "")
	t.Setenv("AWS_OIDC_AUTH_PROFILE", "")

	setupConfig(t, tmp, `{"profiles":{"a":{},"b":{}}}`)

	os.Args = []string{"credential-process"}
	if code := run(); code != 1 {
		t.Errorf("expected exit 1 for missing profile, got %d", code)
	}
}

func TestRun_ProfileFromEnv(t *testing.T) {
	resetFlags()
	tmp := t.TempDir()
	t.Setenv("HOME", tmp)
	t.Setenv("USERPROFILE", tmp)
	t.Setenv("AWS_OIDC_AUTH_PROFILE", "envprofile")
	t.Setenv("AWS_PROFILE", "")

	setupConfig(t, tmp, `{"profiles":{
		"envprofile": {
			"credential_storage": "session",
			"federation_type": "cognito",
			"aws_region": "us-east-1",
			"identity_pool_id": "us-east-1:pool"
		}
	}}`)
	future := time.Now().Add(1 * time.Hour).UTC().Format(time.RFC3339)
	writeCreds(t, tmp, "envprofile", future)

	os.Args = []string{"credential-process", "--check-expiration"}
	if code := run(); code != 0 {
		t.Errorf("expected exit 0, got %d", code)
	}
}

func TestRun_MissingConfigFile(t *testing.T) {
	resetFlags()
	tmp := t.TempDir()
	t.Setenv("HOME", tmp)
	t.Setenv("USERPROFILE", tmp)
	t.Setenv("AWS_PROFILE", "")
	t.Setenv("AWS_OIDC_AUTH_PROFILE", "")

	os.Args = []string{"credential-process", "--profile", "default", "--check-expiration"}
	if code := run(); code != 1 {
		t.Errorf("expected exit 1 for missing config, got %d", code)
	}
}
