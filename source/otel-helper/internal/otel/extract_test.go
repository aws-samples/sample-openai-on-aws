package otel

import (
	"strings"
	"testing"

	"otel-helper/internal/jwt"
)

func TestExtractUserInfo_AllFields(t *testing.T) {
	claims := jwt.Claims{
		"email":            "user@example.com",
		"sub":              "user-id-123",
		"cognito:username": "jdoe",
		"iss":              "https://dev-12345.okta.com",
		"department":       "engineering",
		"team":             "platform",
		"cost_center":      "CC-100",
		"manager":          "boss@example.com",
		"location":         "NYC",
		"role":             "developer",
		"aud":              "client-id-abc",
	}

	info := ExtractUserInfo(claims)

	if info.Email != "user@example.com" {
		t.Errorf("Email = %q, want user@example.com", info.Email)
	}
	if info.Username != "jdoe" {
		t.Errorf("Username = %q, want jdoe", info.Username)
	}
	if info.OrganizationID != "okta" {
		t.Errorf("OrganizationID = %q, want okta", info.OrganizationID)
	}

	// UUID format: 8-4-4-4-12
	parts := strings.Split(info.UserID, "-")
	if len(parts) != 5 || len(parts[0]) != 8 || len(parts[4]) != 12 {
		t.Errorf("UserID format incorrect: %q", info.UserID)
	}
}

func TestExtractUserInfo_Defaults(t *testing.T) {
	claims := jwt.Claims{}
	info := ExtractUserInfo(claims)

	if info.Email != "unknown@example.com" {
		t.Errorf("Email = %q, want unknown@example.com", info.Email)
	}
	if info.Department != "unspecified" {
		t.Errorf("Department = %q, want unspecified", info.Department)
	}
	if info.Team != "default-team" {
		t.Errorf("Team = %q, want default-team", info.Team)
	}
}

func TestExtractUserInfo_ConsistentHash(t *testing.T) {
	claims1 := jwt.Claims{"sub": "user-123"}
	claims2 := jwt.Claims{"sub": "user-123"}

	info1 := ExtractUserInfo(claims1)
	info2 := ExtractUserInfo(claims2)

	if info1.UserID != info2.UserID {
		t.Errorf("Same sub should produce same UserID: %q vs %q", info1.UserID, info2.UserID)
	}

	claims3 := jwt.Claims{"sub": "different-user"}
	info3 := ExtractUserInfo(claims3)
	if info1.UserID == info3.UserID {
		t.Error("Different subs should produce different UserIDs")
	}
}
