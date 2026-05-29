package sso

import (
	"crypto/sha1"
	"encoding/hex"
	"encoding/json"
	"os"
	"path/filepath"
	"time"
)

type CachedToken struct {
	StartURL              string `json:"startUrl"`
	Region                string `json:"region"`
	AccessToken           string `json:"accessToken"`
	ExpiresAt             string `json:"expiresAt"`
	ClientID              string `json:"clientId,omitempty"`
	ClientSecret          string `json:"clientSecret,omitempty"`
	RegistrationExpiresAt string `json:"registrationExpiresAt,omitempty"`
}

func ReadCachedToken(startURL string) (*CachedToken, error) {
	path, err := cacheFilePath(startURL)
	if err != nil {
		return nil, err
	}

	data, err := os.ReadFile(path)
	if err != nil {
		return nil, err
	}

	var token CachedToken
	if err := json.Unmarshal(data, &token); err != nil {
		return nil, err
	}

	return &token, nil
}

func WriteCachedToken(token *CachedToken) error {
	dir, err := cacheDir()
	if err != nil {
		return err
	}
	if err := os.MkdirAll(dir, 0700); err != nil {
		return err
	}

	path, err := cacheFilePath(token.StartURL)
	if err != nil {
		return err
	}

	data, err := json.MarshalIndent(token, "", "  ")
	if err != nil {
		return err
	}

	return os.WriteFile(path, data, 0600)
}

func IsTokenValid(token *CachedToken) bool {
	if token == nil || token.AccessToken == "" || token.ExpiresAt == "" {
		return false
	}

	exp, err := parseExpiresAt(token.ExpiresAt)
	if err != nil {
		return false
	}

	return time.Now().Add(5 * time.Minute).Before(exp)
}

func cacheDir() (string, error) {
	home, err := os.UserHomeDir()
	if err != nil {
		return "", err
	}
	return filepath.Join(home, ".aws", "sso", "cache"), nil
}

func cacheFilePath(startURL string) (string, error) {
	dir, err := cacheDir()
	if err != nil {
		return "", err
	}
	h := sha1.Sum([]byte(startURL))
	return filepath.Join(dir, hex.EncodeToString(h[:])+".json"), nil
}

func parseExpiresAt(s string) (time.Time, error) {
	// AWS CLI uses multiple formats
	formats := []string{
		"2006-01-02T15:04:05UTC",
		time.RFC3339,
		"2006-01-02T15:04:05Z",
		"2006-01-02T15:04:05Z07:00",
	}
	for _, f := range formats {
		if t, err := time.Parse(f, s); err == nil {
			return t, nil
		}
	}
	return time.Time{}, &time.ParseError{Value: s, Message: "unrecognized time format"}
}
