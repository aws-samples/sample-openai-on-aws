package sso

import (
	"testing"
	"time"
)

func TestWriteAndReadCachedToken(t *testing.T) {
	tmp := t.TempDir()
	t.Setenv("HOME", tmp)
	t.Setenv("USERPROFILE", tmp)

	future := time.Now().Add(1 * time.Hour).UTC().Format("2006-01-02T15:04:05UTC")
	tok := &CachedToken{
		StartURL:    "https://d-test.awsapps.com/start",
		Region:      "us-east-1",
		AccessToken: "access-token-value",
		ExpiresAt:   future,
	}

	if err := WriteCachedToken(tok); err != nil {
		t.Fatalf("WriteCachedToken: %v", err)
	}

	got, err := ReadCachedToken("https://d-test.awsapps.com/start")
	if err != nil {
		t.Fatalf("ReadCachedToken: %v", err)
	}
	if got.AccessToken != "access-token-value" {
		t.Errorf("AccessToken: got %q", got.AccessToken)
	}
	if got.Region != "us-east-1" {
		t.Errorf("Region: got %q", got.Region)
	}
}

func TestIsTokenValid(t *testing.T) {
	future := time.Now().Add(1 * time.Hour).UTC().Format("2006-01-02T15:04:05UTC")
	past := time.Now().Add(-1 * time.Hour).UTC().Format("2006-01-02T15:04:05UTC")
	near := time.Now().Add(3 * time.Minute).UTC().Format("2006-01-02T15:04:05UTC")

	tests := []struct {
		name  string
		tok   *CachedToken
		valid bool
	}{
		{"nil token", nil, false},
		{"empty access token", &CachedToken{ExpiresAt: future}, false},
		{"empty expiresAt", &CachedToken{AccessToken: "t"}, false},
		{"future valid", &CachedToken{AccessToken: "t", ExpiresAt: future}, true},
		{"past expired", &CachedToken{AccessToken: "t", ExpiresAt: past}, false},
		{"within 5-min buffer", &CachedToken{AccessToken: "t", ExpiresAt: near}, false},
		{"invalid format", &CachedToken{AccessToken: "t", ExpiresAt: "not-a-date"}, false},
	}

	for _, tc := range tests {
		t.Run(tc.name, func(t *testing.T) {
			if got := IsTokenValid(tc.tok); got != tc.valid {
				t.Errorf("IsTokenValid=%v, want %v", got, tc.valid)
			}
		})
	}
}

func TestIsTokenValid_RFC3339Format(t *testing.T) {
	future := time.Now().Add(1 * time.Hour).UTC().Format(time.RFC3339)
	tok := &CachedToken{AccessToken: "t", ExpiresAt: future}
	if !IsTokenValid(tok) {
		t.Error("expected valid for RFC3339 future timestamp")
	}
}

func TestReadCachedToken_NoFile(t *testing.T) {
	tmp := t.TempDir()
	t.Setenv("HOME", tmp)
	t.Setenv("USERPROFILE", tmp)

	_, err := ReadCachedToken("https://d-nonexistent.awsapps.com/start")
	if err == nil {
		t.Error("expected error for absent cache file")
	}
}
