package otel

import (
	"fmt"
	"os"
	"path/filepath"
	"testing"
	"time"
)

func TestWriteAndReadCachedHeaders(t *testing.T) {
	tmpDir := t.TempDir()
	t.Setenv("HOME", tmpDir)
	t.Setenv("USERPROFILE", tmpDir)

	profile := "test-profile"
	headers := map[string]string{
		"x-user-email": "test@example.com",
		"x-user-id":    "12345",
	}
	tokenExp := time.Now().Unix() + 3600

	err := WriteCachedHeaders(profile, headers, tokenExp)
	if err != nil {
		t.Fatalf("WriteCachedHeaders failed: %v", err)
	}

	cacheDir := filepath.Join(tmpDir, ".aws-oidc-session")
	if _, err := os.Stat(filepath.Join(cacheDir, profile+"-otel-headers.json")); err != nil {
		t.Errorf("json cache file missing: %v", err)
	}
	if _, err := os.Stat(filepath.Join(cacheDir, profile+"-otel-headers.raw")); err != nil {
		t.Errorf("raw cache file missing: %v", err)
	}

	cached, err := ReadCachedHeaders(profile)
	if err != nil {
		t.Fatalf("ReadCachedHeaders failed: %v", err)
	}
	if cached["x-user-email"] != "test@example.com" {
		t.Errorf("x-user-email = %q, want test@example.com", cached["x-user-email"])
	}
}

func TestReadCachedHeaders_Expired(t *testing.T) {
	// Under the new policy, populated headers are served past expiry (they are
	// static user attributes). The old 10-min buffer no longer applies.
	tmpDir := t.TempDir()
	t.Setenv("HOME", tmpDir)
	t.Setenv("USERPROFILE", tmpDir)

	profile := "expired-profile"
	headers := map[string]string{"x-user-email": "test@example.com"}
	tokenExp := time.Now().Unix() - 1 // already expired

	_ = WriteCachedHeaders(profile, headers, tokenExp)

	cached, err := ReadCachedHeaders(profile)
	if err != nil {
		t.Errorf("populated headers should be served past expiry, got error: %v", err)
	}
	if cached["x-user-email"] != "test@example.com" {
		t.Errorf("x-user-email = %q, want test@example.com", cached["x-user-email"])
	}
}

func TestReadCachedHeaders_Missing(t *testing.T) {
	tmpDir := t.TempDir()
	t.Setenv("HOME", tmpDir)
	t.Setenv("USERPROFILE", tmpDir)

	_, err := ReadCachedHeaders("nonexistent")
	if err == nil {
		t.Error("expected error for missing cache")
	}
}

func TestReadCachedHeaders_EmptyHeadersMapIsHit(t *testing.T) {
	tmpDir := t.TempDir()
	t.Setenv("HOME", tmpDir)
	t.Setenv("USERPROFILE", tmpDir)

	profile := "empty-headers-hit"
	headers := map[string]string{}
	tokenExp := int64(9999999999)

	if err := WriteCachedHeaders(profile, headers, tokenExp); err != nil {
		t.Fatalf("WriteCachedHeaders failed: %v", err)
	}

	cached, err := ReadCachedHeaders(profile)
	if err != nil {
		t.Fatalf("expected empty-headers map to be a cache hit, got error: %v", err)
	}
	if cached == nil {
		t.Error("expected non-nil map, got nil")
	}
	if len(cached) != 0 {
		t.Errorf("expected empty map, got %v", cached)
	}
}

func TestReadCachedHeaders_ExpiredEmptyHeadersIsMiss(t *testing.T) {
	tmpDir := t.TempDir()
	t.Setenv("HOME", tmpDir)
	t.Setenv("USERPROFILE", tmpDir)

	profile := "empty-headers-miss"
	headers := map[string]string{}
	tokenExp := time.Now().Unix() - 1 // already expired

	if err := WriteCachedHeaders(profile, headers, tokenExp); err != nil {
		t.Fatalf("WriteCachedHeaders failed: %v", err)
	}

	_, err := ReadCachedHeaders(profile)
	if err == nil {
		t.Error("expected error for expired empty-headers cache")
	}
}

func TestReadCachedHeaders_PopulatedHeadersServedPastExpiry(t *testing.T) {
	tmpDir := t.TempDir()
	t.Setenv("HOME", tmpDir)
	t.Setenv("USERPROFILE", tmpDir)

	profile := "populated-past-expiry"
	headers := map[string]string{"x-user-email": "real@user.com"}
	tokenExp := int64(1000) // far in the past

	if err := WriteCachedHeaders(profile, headers, tokenExp); err != nil {
		t.Fatalf("WriteCachedHeaders failed: %v", err)
	}

	cached, err := ReadCachedHeaders(profile)
	if err != nil {
		t.Fatalf("populated headers must be served past expiry, got error: %v", err)
	}
	if cached["x-user-email"] != "real@user.com" {
		t.Errorf("x-user-email = %q, want real@user.com", cached["x-user-email"])
	}
}

func TestWriteTwiceOverwritesCacheFile(t *testing.T) {
	tmpDir := t.TempDir()
	t.Setenv("HOME", tmpDir)
	t.Setenv("USERPROFILE", tmpDir)

	profile := "overwrite-test"
	first := map[string]string{"x-user-email": "first@example.com"}
	second := map[string]string{"x-user-email": "second@example.com"}
	tokenExp := int64(9999999999)

	if err := WriteCachedHeaders(profile, first, tokenExp); err != nil {
		t.Fatalf("first WriteCachedHeaders failed: %v", err)
	}
	if err := WriteCachedHeaders(profile, second, tokenExp); err != nil {
		t.Fatalf("second WriteCachedHeaders failed: %v", err)
	}

	cached, err := ReadCachedHeaders(profile)
	if err != nil {
		t.Fatalf("ReadCachedHeaders failed: %v", err)
	}
	if cached["x-user-email"] != "second@example.com" {
		t.Errorf("second write should win; x-user-email = %q, want second@example.com", cached["x-user-email"])
	}
}

func TestReadCachedHeaders_UntimedEmptyHeadersIsMiss(t *testing.T) {
	tmpDir := t.TempDir()
	t.Setenv("HOME", tmpDir)
	t.Setenv("USERPROFILE", tmpDir)

	profile := "untimed-empty"
	headers := map[string]string{}
	tokenExp := int64(0) // untimed

	if err := WriteCachedHeaders(profile, headers, tokenExp); err != nil {
		t.Fatalf("WriteCachedHeaders failed: %v", err)
	}

	_, err := ReadCachedHeaders(profile)
	if err == nil {
		t.Error("expected error for untimed empty-headers cache")
	}
}

func TestEmptyHeadersWriteSafe(t *testing.T) {
	type tc struct {
		name     string
		setup    func(dir string)
		wantSafe bool
	}
	tests := []tc{
		{
			name:     "absent file is safe",
			setup:    func(dir string) {},
			wantSafe: true,
		},
		{
			name: "populated current-schema is NOT safe",
			setup: func(dir string) {
				data := fmt.Sprintf(`{"schema_version":%d,"headers":{"x-user-email":"a@b.com"},"token_exp":9999999999,"cached_at":1}`, currentCacheSchemaVersion)
				_ = atomicWrite(dir+"/safe-test-otel-headers.json", []byte(data))
			},
			wantSafe: false,
		},
		{
			name: "empty current-schema is safe",
			setup: func(dir string) {
				data := fmt.Sprintf(`{"schema_version":%d,"headers":{},"token_exp":9999999999,"cached_at":1}`, currentCacheSchemaVersion)
				_ = atomicWrite(dir+"/safe-test-otel-headers.json", []byte(data))
			},
			wantSafe: true,
		},
		{
			name: "stale schema is safe",
			setup: func(dir string) {
				data := `{"schema_version":0,"headers":{"x-user-email":"a@b.com"},"token_exp":9999999999,"cached_at":1}`
				_ = atomicWrite(dir+"/safe-test-otel-headers.json", []byte(data))
			},
			wantSafe: true,
		},
		{
			name: "unparseable is NOT safe",
			setup: func(dir string) {
				_ = atomicWrite(dir+"/safe-test-otel-headers.json", []byte("not json {{"))
			},
			wantSafe: false,
		},
	}

	for _, tt := range tests {
		t.Run(tt.name, func(t *testing.T) {
			tmpDir := t.TempDir()
			t.Setenv("HOME", tmpDir)
			t.Setenv("USERPROFILE", tmpDir)

			cacheDir := tmpDir + "/.aws-oidc-session"
			if err := os.MkdirAll(cacheDir, 0700); err != nil {
				t.Fatalf("mkdir failed: %v", err)
			}
			tt.setup(cacheDir)

			got := EmptyHeadersWriteSafe("safe-test")
			if got != tt.wantSafe {
				t.Errorf("EmptyHeadersWriteSafe = %v, want %v", got, tt.wantSafe)
			}
		})
	}
}

