package storage

import (
	"encoding/json"
	"os"
	"path/filepath"
	"time"
)

// RefreshTokenData is the on-disk or keyring format for a cached refresh token.
type RefreshTokenData struct {
	Token     string `json:"refresh_token"`
	Profile   string `json:"profile"`
	UpdatedAt int64  `json:"updated_at"`
}

// SaveRefreshToken persists the OIDC refresh_token for a profile.
func SaveRefreshToken(profile, storageType, token string) error {
	if token == "" {
		return nil
	}

	data := &RefreshTokenData{
		Token:     token,
		Profile:   profile,
		UpdatedAt: time.Now().Unix(),
	}

	if storageType == "keyring" {
		return SaveRefreshTokenToKeyring(data, profile)
	}
	return saveRefreshTokenToFile(data, profile)
}

// LoadRefreshToken retrieves the cached refresh_token for a profile.
// Returns an empty string if no token is available.
func LoadRefreshToken(profile, storageType string) string {
	if storageType == "keyring" {
		data, err := ReadRefreshTokenFromKeyring(profile)
		if err != nil || data == nil {
			return ""
		}
		return data.Token
	}

	data, err := readRefreshTokenFromFile(profile)
	if err != nil || data == nil {
		return ""
	}
	return data.Token
}

// ClearRefreshToken removes any cached refresh token for a profile.
func ClearRefreshToken(profile, storageType string) error {
	if storageType == "keyring" {
		return SaveRefreshTokenToKeyring(&RefreshTokenData{Profile: profile}, profile)
	}

	path := filepath.Join(sessionDir(), profile+"-refresh.json")
	if err := os.Remove(path); err != nil && !os.IsNotExist(err) {
		return err
	}
	return nil
}

func readRefreshTokenFromFile(profile string) (*RefreshTokenData, error) {
	path := filepath.Join(sessionDir(), profile+"-refresh.json")
	raw, err := os.ReadFile(path)
	if err != nil {
		return nil, err
	}

	var data RefreshTokenData
	if err := json.Unmarshal(raw, &data); err != nil {
		return nil, err
	}
	return &data, nil
}

func saveRefreshTokenToFile(data *RefreshTokenData, profile string) error {
	dir := sessionDir()
	if err := os.MkdirAll(dir, 0700); err != nil {
		return err
	}

	raw, err := json.Marshal(data)
	if err != nil {
		return err
	}

	path := filepath.Join(dir, profile+"-refresh.json")
	tmpPath := path + ".tmp"
	if err := os.WriteFile(tmpPath, raw, 0600); err != nil {
		return err
	}
	return os.Rename(tmpPath, path)
}
