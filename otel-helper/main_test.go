package main

import (
	"encoding/json"
	"os"
	"path/filepath"
	"testing"
)

func TestRun_NoToken_EmitsEmptyHeadersAndExitsZero(t *testing.T) {
	tmpDir := t.TempDir()
	t.Setenv("HOME", tmpDir)
	t.Setenv("USERPROFILE", tmpDir)
	t.Setenv("AWS_PROFILE", "default")
	t.Setenv("AWS_OIDC_AUTH_MONITORING_TOKEN", "")

	code := run(false)
	if code != 0 {
		t.Fatalf("run() = %d, want 0", code)
	}

	cacheFile := filepath.Join(tmpDir, ".aws-oidc-session", "default-otel-headers.json")
	data, err := os.ReadFile(cacheFile)
	if err != nil {
		t.Fatalf("cache file missing: %v", err)
	}

	var entry struct {
		Headers  map[string]string `json:"headers"`
		TokenExp int64             `json:"token_exp"`
	}
	if err := json.Unmarshal(data, &entry); err != nil {
		t.Fatalf("invalid JSON in cache: %v", err)
	}
	if entry.Headers == nil {
		t.Error("headers should be non-nil empty map, got nil")
	}
	if len(entry.Headers) != 0 {
		t.Errorf("headers should be empty map, got %v", entry.Headers)
	}
	if entry.TokenExp <= 0 {
		t.Errorf("token_exp should be > 0, got %d", entry.TokenExp)
	}
}

func TestRun_TestMode_NoToken_DoesNotWriteCache(t *testing.T) {
	tmpDir := t.TempDir()
	t.Setenv("HOME", tmpDir)
	t.Setenv("USERPROFILE", tmpDir)
	t.Setenv("AWS_PROFILE", "default")
	t.Setenv("AWS_OIDC_AUTH_MONITORING_TOKEN", "")

	code := run(true)
	if code != 0 {
		t.Fatalf("run(testMode=true) = %d, want 0", code)
	}

	cacheFile := filepath.Join(tmpDir, ".aws-oidc-session", "default-otel-headers.json")
	if _, err := os.Stat(cacheFile); !os.IsNotExist(err) {
		t.Error("cache file should NOT exist in test mode")
	}
}

func TestRun_FreshEmptyCache_ServedViaLayer1(t *testing.T) {
	tmpDir := t.TempDir()
	t.Setenv("HOME", tmpDir)
	t.Setenv("USERPROFILE", tmpDir)
	t.Setenv("AWS_PROFILE", "default")
	t.Setenv("AWS_OIDC_AUTH_MONITORING_TOKEN", "")

	cacheDir := filepath.Join(tmpDir, ".aws-oidc-session")
	if err := os.MkdirAll(cacheDir, 0700); err != nil {
		t.Fatalf("mkdir: %v", err)
	}
	cacheFile := filepath.Join(cacheDir, "default-otel-headers.json")
	seedData := []byte(`{"schema_version":1,"headers":{},"token_exp":9999999999,"cached_at":1000}`)
	if err := os.WriteFile(cacheFile, seedData, 0600); err != nil {
		t.Fatalf("seed write: %v", err)
	}

	code := run(false)
	if code != 0 {
		t.Fatalf("run() = %d, want 0", code)
	}

	after, err := os.ReadFile(cacheFile)
	if err != nil {
		t.Fatalf("reading cache after run: %v", err)
	}
	if string(after) != string(seedData) {
		t.Errorf("cache was rewritten; want identical bytes\ngot:  %s\nwant: %s", after, seedData)
	}
}

func TestRun_PopulatedExpiredEntry_ServedNotRewritten(t *testing.T) {
	tmpDir := t.TempDir()
	t.Setenv("HOME", tmpDir)
	t.Setenv("USERPROFILE", tmpDir)
	t.Setenv("AWS_PROFILE", "default")
	t.Setenv("AWS_OIDC_AUTH_MONITORING_TOKEN", "")

	cacheDir := filepath.Join(tmpDir, ".aws-oidc-session")
	if err := os.MkdirAll(cacheDir, 0700); err != nil {
		t.Fatalf("mkdir: %v", err)
	}
	cacheFile := filepath.Join(cacheDir, "default-otel-headers.json")
	seedData := []byte(`{"schema_version":1,"headers":{"x-user-email":"real@user.com"},"token_exp":1000,"cached_at":500}`)
	if err := os.WriteFile(cacheFile, seedData, 0600); err != nil {
		t.Fatalf("seed write: %v", err)
	}

	code := run(false)
	if code != 0 {
		t.Fatalf("run() = %d, want 0", code)
	}

	data, err := os.ReadFile(cacheFile)
	if err != nil {
		t.Fatalf("reading cache after run: %v", err)
	}
	var entry struct {
		Headers map[string]string `json:"headers"`
	}
	if err := json.Unmarshal(data, &entry); err != nil {
		t.Fatalf("invalid JSON: %v", err)
	}
	if entry.Headers["x-user-email"] != "real@user.com" {
		t.Errorf("x-user-email = %q, want real@user.com (entry should not be clobbered)", entry.Headers["x-user-email"])
	}
}
