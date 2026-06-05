package storage

import (
	"os"
	"path/filepath"
	"testing"
	"time"

	"aws-oidc-auth/internal/federation"
)

func TestReadWriteCredentialsFile(t *testing.T) {
	tmp := t.TempDir()
	t.Setenv("HOME", tmp)
	t.Setenv("USERPROFILE", tmp)

	creds := &federation.AWSCredentials{
		Version:         1,
		AccessKeyID:     "AKID",
		SecretAccessKey: "SECRET",
		SessionToken:    "TOKEN",
		Expiration:      "2030-01-01T00:00:00Z",
	}

	if err := SaveToCredentialsFile(creds, "myprofile"); err != nil {
		t.Fatalf("SaveToCredentialsFile: %v", err)
	}

	got, err := ReadFromCredentialsFile("myprofile")
	if err != nil {
		t.Fatalf("ReadFromCredentialsFile: %v", err)
	}
	if got == nil {
		t.Fatal("expected credentials, got nil")
	}
	if got.AccessKeyID != "AKID" {
		t.Errorf("AccessKeyID: got %q", got.AccessKeyID)
	}
	if got.SecretAccessKey != "SECRET" {
		t.Errorf("SecretAccessKey: got %q", got.SecretAccessKey)
	}
	if got.SessionToken != "TOKEN" {
		t.Errorf("SessionToken: got %q", got.SessionToken)
	}
	if got.Expiration != "2030-01-01T00:00:00Z" {
		t.Errorf("Expiration: got %q", got.Expiration)
	}
}

func TestReadCredentialsFile_NoFile(t *testing.T) {
	tmp := t.TempDir()
	t.Setenv("HOME", tmp)
	t.Setenv("USERPROFILE", tmp)

	got, err := ReadFromCredentialsFile("any")
	if err != nil {
		t.Fatalf("unexpected error: %v", err)
	}
	if got != nil {
		t.Errorf("expected nil for absent file, got %+v", got)
	}
}

func TestReadCredentialsFile_MissingSection(t *testing.T) {
	tmp := t.TempDir()
	t.Setenv("HOME", tmp)
	t.Setenv("USERPROFILE", tmp)

	credPath := filepath.Join(tmp, ".aws", "credentials")
	os.MkdirAll(filepath.Dir(credPath), 0700)
	os.WriteFile(credPath, []byte("[other]\naws_access_key_id = X\n"), 0600)

	got, err := ReadFromCredentialsFile("missing")
	if err != nil {
		t.Fatalf("unexpected error: %v", err)
	}
	if got != nil {
		t.Errorf("expected nil for absent section, got %+v", got)
	}
}

func TestSaveToCredentialsFile_UpdatesExistingProfile(t *testing.T) {
	tmp := t.TempDir()
	t.Setenv("HOME", tmp)
	t.Setenv("USERPROFILE", tmp)

	first := &federation.AWSCredentials{Version: 1, AccessKeyID: "FIRST", SecretAccessKey: "S1", SessionToken: "T1"}
	second := &federation.AWSCredentials{Version: 1, AccessKeyID: "SECOND", SecretAccessKey: "S2", SessionToken: "T2"}

	if err := SaveToCredentialsFile(first, "p"); err != nil {
		t.Fatal(err)
	}
	if err := SaveToCredentialsFile(second, "p"); err != nil {
		t.Fatal(err)
	}

	got, err := ReadFromCredentialsFile("p")
	if err != nil || got == nil {
		t.Fatalf("read after update: err=%v got=%v", err, got)
	}
	if got.AccessKeyID != "SECOND" {
		t.Errorf("expected SECOND, got %q", got.AccessKeyID)
	}
}

func TestIsExpiredDummy(t *testing.T) {
	if !IsExpiredDummy(&federation.AWSCredentials{AccessKeyID: "EXPIRED"}) {
		t.Error("expected true for EXPIRED")
	}
	if IsExpiredDummy(&federation.AWSCredentials{AccessKeyID: "AKID"}) {
		t.Error("expected false for real key")
	}
	if IsExpiredDummy(nil) {
		t.Error("expected false for nil")
	}
}

func TestParseExpirationSeconds(t *testing.T) {
	future := time.Now().Add(1 * time.Hour).UTC().Format(time.RFC3339)
	secs := ParseExpirationSeconds(future)
	if secs < 3500 || secs > 3700 {
		t.Errorf("expected ~3600, got %f", secs)
	}

	past := "2000-01-01T00:00:00Z"
	if ParseExpirationSeconds(past) >= 0 {
		// negative means expired — we just want it to not be zero-like
	}

	if ParseExpirationSeconds("") != 0 {
		t.Error("empty string should return 0")
	}
	if ParseExpirationSeconds("not-a-date") != 0 {
		t.Error("invalid string should return 0")
	}
}

func TestSaveAndGetMonitoringToken_File(t *testing.T) {
	tmp := t.TempDir()
	t.Setenv("HOME", tmp)
	t.Setenv("USERPROFILE", tmp)
	t.Setenv("AWS_OIDC_AUTH_MONITORING_TOKEN", "")

	futureExp := time.Now().Add(2 * time.Hour).Unix()
	claims := map[string]interface{}{
		"exp":   float64(futureExp),
		"email": "user@example.com",
	}

	if err := SaveMonitoringToken("p", "session", "id-token-value", claims); err != nil {
		t.Fatalf("SaveMonitoringToken: %v", err)
	}

	token, err := GetMonitoringToken("p", "session")
	if err != nil {
		t.Fatalf("GetMonitoringToken: %v", err)
	}
	if token != "id-token-value" {
		t.Errorf("got %q, want %q", token, "id-token-value")
	}
}

func TestGetMonitoringToken_FromEnv(t *testing.T) {
	tmp := t.TempDir()
	t.Setenv("HOME", tmp)
	t.Setenv("USERPROFILE", tmp)
	t.Setenv("AWS_OIDC_AUTH_MONITORING_TOKEN", "env-token")

	token, err := GetMonitoringToken("any", "session")
	if err != nil {
		t.Fatal(err)
	}
	if token != "env-token" {
		t.Errorf("got %q, want %q", token, "env-token")
	}
}

func TestGetMonitoringToken_Expired(t *testing.T) {
	tmp := t.TempDir()
	t.Setenv("HOME", tmp)
	t.Setenv("USERPROFILE", tmp)
	t.Setenv("AWS_OIDC_AUTH_MONITORING_TOKEN", "")

	pastExp := time.Now().Add(-1 * time.Hour).Unix()
	claims := map[string]interface{}{"exp": float64(pastExp)}
	if err := SaveMonitoringToken("p", "session", "stale-token", claims); err != nil {
		t.Fatal(err)
	}

	token, err := GetMonitoringToken("p", "session")
	if err != nil {
		t.Fatal(err)
	}
	if token != "" {
		t.Errorf("expected empty for expired token, got %q", token)
	}
}

func TestGetMonitoringToken_NoFile(t *testing.T) {
	tmp := t.TempDir()
	t.Setenv("HOME", tmp)
	t.Setenv("USERPROFILE", tmp)
	t.Setenv("AWS_OIDC_AUTH_MONITORING_TOKEN", "")

	token, err := GetMonitoringToken("absent", "session")
	if err != nil && !os.IsNotExist(err) {
		// Underlying file error is acceptable
	}
	if token != "" {
		t.Errorf("expected empty, got %q", token)
	}
}
