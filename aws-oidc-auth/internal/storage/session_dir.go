package storage

import (
	"os"
	"path/filepath"
)

func sessionDir() string {
	home, _ := os.UserHomeDir()
	return filepath.Join(home, ".aws-oidc-session")
}
