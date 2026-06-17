package storage

import (
	"encoding/json"
	"os"
	"path/filepath"
	"runtime"
	"testing"
	"time"
)

func TestSaveAndLoadRefreshToken(t *testing.T) {
	tmpDir := t.TempDir()
	t.Setenv("HOME", tmpDir)
	t.Setenv("USERPROFILE", tmpDir)

	if err := SaveRefreshToken("TestProfile", "session", "rt_test_token_abc123"); err != nil {
		t.Fatalf("SaveRefreshToken: %v", err)
	}

	if got := LoadRefreshToken("TestProfile", "session"); got != "rt_test_token_abc123" {
		t.Fatalf("LoadRefreshToken() = %q, want %q", got, "rt_test_token_abc123")
	}

	path := filepath.Join(tmpDir, ".aws-oidc-session", "TestProfile-refresh.json")
	info, err := os.Stat(path)
	if err != nil {
		t.Fatalf("Stat(%s): %v", path, err)
	}
	if runtime.GOOS != "windows" && info.Mode().Perm() != 0600 {
		t.Fatalf("permissions = %o, want 0600", info.Mode().Perm())
	}

	raw, err := os.ReadFile(path)
	if err != nil {
		t.Fatalf("ReadFile(%s): %v", path, err)
	}

	var data map[string]interface{}
	if err := json.Unmarshal(raw, &data); err != nil {
		t.Fatalf("Unmarshal(refresh token JSON): %v", err)
	}
	if data["refresh_token"] != "rt_test_token_abc123" {
		t.Fatalf("refresh_token = %v, want %q", data["refresh_token"], "rt_test_token_abc123")
	}
	if data["profile"] != "TestProfile" {
		t.Fatalf("profile = %v, want %q", data["profile"], "TestProfile")
	}
}

func TestLoadRefreshToken_Missing(t *testing.T) {
	tmpDir := t.TempDir()
	t.Setenv("HOME", tmpDir)
	t.Setenv("USERPROFILE", tmpDir)

	if got := LoadRefreshToken("MissingProfile", "session"); got != "" {
		t.Fatalf("LoadRefreshToken() = %q, want empty string", got)
	}
}

func TestSaveRefreshToken_EmptyToken(t *testing.T) {
	tmpDir := t.TempDir()
	t.Setenv("HOME", tmpDir)
	t.Setenv("USERPROFILE", tmpDir)

	if err := SaveRefreshToken("TestProfile", "session", ""); err != nil {
		t.Fatalf("SaveRefreshToken(empty): %v", err)
	}

	path := filepath.Join(tmpDir, ".aws-oidc-session", "TestProfile-refresh.json")
	if _, err := os.Stat(path); !os.IsNotExist(err) {
		t.Fatalf("expected no refresh token file, got err=%v", err)
	}
}

func TestClearRefreshToken(t *testing.T) {
	tmpDir := t.TempDir()
	t.Setenv("HOME", tmpDir)
	t.Setenv("USERPROFILE", tmpDir)

	if err := SaveRefreshToken("TestProfile", "session", "rt_to_be_cleared"); err != nil {
		t.Fatalf("SaveRefreshToken: %v", err)
	}
	if err := ClearRefreshToken("TestProfile", "session"); err != nil {
		t.Fatalf("ClearRefreshToken: %v", err)
	}

	if got := LoadRefreshToken("TestProfile", "session"); got != "" {
		t.Fatalf("LoadRefreshToken() after clear = %q, want empty string", got)
	}
}

func TestClearMonitoringToken(t *testing.T) {
	tmpDir := t.TempDir()
	t.Setenv("HOME", tmpDir)
	t.Setenv("USERPROFILE", tmpDir)
	t.Setenv("AWS_OIDC_AUTH_MONITORING_TOKEN", "")

	claims := map[string]interface{}{
		"exp": float64(time.Now().Add(2 * time.Hour).Unix()),
	}
	if err := SaveMonitoringToken("TestProfile", "session", "monitoring-token", claims); err != nil {
		t.Fatalf("SaveMonitoringToken: %v", err)
	}
	if err := ClearMonitoringToken("TestProfile", "session"); err != nil {
		t.Fatalf("ClearMonitoringToken: %v", err)
	}

	token, err := GetMonitoringToken("TestProfile", "session")
	if err != nil {
		t.Fatalf("GetMonitoringToken: %v", err)
	}
	if token != "" {
		t.Fatalf("GetMonitoringToken() = %q, want empty string", token)
	}
}
