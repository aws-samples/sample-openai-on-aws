package config

import (
	"os"
	"path/filepath"
	"testing"
)

func writeConfig(t *testing.T, dir, content string) {
	t.Helper()
	p := filepath.Join(dir, "aws-oidc-auth", "config.json")
	if err := os.MkdirAll(filepath.Dir(p), 0700); err != nil {
		t.Fatal(err)
	}
	if err := os.WriteFile(p, []byte(content), 0600); err != nil {
		t.Fatal(err)
	}
}

func TestLoadProfile_NewFormat(t *testing.T) {
	tmp := t.TempDir()
	t.Setenv("HOME", tmp)
	t.Setenv("USERPROFILE", tmp)

	writeConfig(t, tmp, `{
		"profiles": {
			"default": {
				"provider_domain": "dev-123.okta.com",
				"client_id": "abc",
				"aws_region": "us-west-2",
				"credential_storage": "session",
				"federation_type": "cognito",
				"identity_pool_id": "us-west-2:pool-id"
			}
		}
	}`)

	p, err := LoadProfile("default")
	if err != nil {
		t.Fatalf("unexpected error: %v", err)
	}
	if p.ProviderDomain != "dev-123.okta.com" {
		t.Errorf("got ProviderDomain=%q", p.ProviderDomain)
	}
	if p.AWSRegion != "us-west-2" {
		t.Errorf("got AWSRegion=%q", p.AWSRegion)
	}
	if p.CredentialStorage != "session" {
		t.Errorf("got CredentialStorage=%q", p.CredentialStorage)
	}
}

func TestLoadProfile_OldFormat(t *testing.T) {
	tmp := t.TempDir()
	t.Setenv("HOME", tmp)
	t.Setenv("USERPROFILE", tmp)

	writeConfig(t, tmp, `{
		"myprofile": {
			"provider_domain": "login.microsoftonline.com/tenant/v2.0",
			"client_id": "xyz",
			"federation_type": "direct",
			"federated_role_arn": "arn:aws:iam::123:role/R"
		}
	}`)

	p, err := LoadProfile("myprofile")
	if err != nil {
		t.Fatalf("unexpected error: %v", err)
	}
	if p.FederationType != "direct" {
		t.Errorf("got FederationType=%q", p.FederationType)
	}
	if p.MaxSessionDuration != 43200 {
		t.Errorf("direct default MaxSessionDuration: got %d", p.MaxSessionDuration)
	}
}

func TestLoadProfile_LegacyOktaFields(t *testing.T) {
	tmp := t.TempDir()
	t.Setenv("HOME", tmp)
	t.Setenv("USERPROFILE", tmp)

	writeConfig(t, tmp, `{
		"profiles": {
			"legacy": {
				"okta_domain": "company.okta.com",
				"okta_client_id": "old-client"
			}
		}
	}`)

	p, err := LoadProfile("legacy")
	if err != nil {
		t.Fatalf("unexpected error: %v", err)
	}
	if p.ProviderDomain != "company.okta.com" {
		t.Errorf("legacy okta_domain not mapped: got %q", p.ProviderDomain)
	}
	if p.ClientID != "old-client" {
		t.Errorf("legacy okta_client_id not mapped: got %q", p.ClientID)
	}
}

func TestLoadProfile_IdentityPoolNameMapped(t *testing.T) {
	tmp := t.TempDir()
	t.Setenv("HOME", tmp)
	t.Setenv("USERPROFILE", tmp)

	writeConfig(t, tmp, `{
		"profiles": {
			"p": {
				"identity_pool_name": "us-east-1:pool"
			}
		}
	}`)

	p, err := LoadProfile("p")
	if err != nil {
		t.Fatalf("unexpected error: %v", err)
	}
	if p.IdentityPoolID != "us-east-1:pool" {
		t.Errorf("identity_pool_name not promoted: got %q", p.IdentityPoolID)
	}
}

func TestLoadProfile_Defaults(t *testing.T) {
	tmp := t.TempDir()
	t.Setenv("HOME", tmp)
	t.Setenv("USERPROFILE", tmp)

	writeConfig(t, tmp, `{"profiles": {"p": {}}}`)

	p, err := LoadProfile("p")
	if err != nil {
		t.Fatalf("unexpected error: %v", err)
	}
	if p.AWSRegion != "us-east-1" {
		t.Errorf("default region: got %q", p.AWSRegion)
	}
	if p.ProviderType != "auto" {
		t.Errorf("default provider_type: got %q", p.ProviderType)
	}
	if p.CredentialStorage != "session" {
		t.Errorf("default credential_storage: got %q", p.CredentialStorage)
	}
	if p.FederationType != "cognito" {
		t.Errorf("default federation_type: got %q", p.FederationType)
	}
	if p.MaxSessionDuration != 28800 {
		t.Errorf("default MaxSessionDuration: got %d", p.MaxSessionDuration)
	}
}

func TestLoadProfile_FederationTypeAutoDetect(t *testing.T) {
	tmp := t.TempDir()
	t.Setenv("HOME", tmp)
	t.Setenv("USERPROFILE", tmp)

	writeConfig(t, tmp, `{"profiles": {
		"sso":    {"sso_start_url": "https://d-xxx.awsapps.com/start"},
		"direct": {"federated_role_arn": "arn:aws:iam::1:role/R"}
	}}`)

	sso, err := LoadProfile("sso")
	if err != nil {
		t.Fatal(err)
	}
	if sso.FederationType != "sso" {
		t.Errorf("sso auto-detect: got %q", sso.FederationType)
	}

	direct, err := LoadProfile("direct")
	if err != nil {
		t.Fatal(err)
	}
	if direct.FederationType != "direct" {
		t.Errorf("direct auto-detect: got %q", direct.FederationType)
	}
}

func TestLoadProfile_NotFound(t *testing.T) {
	tmp := t.TempDir()
	t.Setenv("HOME", tmp)
	t.Setenv("USERPROFILE", tmp)

	writeConfig(t, tmp, `{"profiles": {"other": {}}}`)

	_, err := LoadProfile("missing")
	if err == nil {
		t.Fatal("expected error for missing profile")
	}
}

func TestLoadProfile_NoConfigFile(t *testing.T) {
	tmp := t.TempDir()
	t.Setenv("HOME", tmp)
	t.Setenv("USERPROFILE", tmp)

	_, err := LoadProfile("any")
	if err == nil {
		t.Fatal("expected error when config.json absent")
	}
}

func TestLoadProfile_InvalidJSON(t *testing.T) {
	tmp := t.TempDir()
	t.Setenv("HOME", tmp)
	t.Setenv("USERPROFILE", tmp)

	writeConfig(t, tmp, `not-json`)

	_, err := LoadProfile("p")
	if err == nil {
		t.Fatal("expected error for invalid JSON")
	}
}

func TestAutoDetectProfile_SingleNewFormat(t *testing.T) {
	tmp := t.TempDir()
	t.Setenv("HOME", tmp)
	t.Setenv("USERPROFILE", tmp)

	writeConfig(t, tmp, `{"profiles": {"only": {}}}`)

	got := AutoDetectProfile()
	if got != "only" {
		t.Errorf("got %q, want %q", got, "only")
	}
}

func TestAutoDetectProfile_SingleOldFormat(t *testing.T) {
	tmp := t.TempDir()
	t.Setenv("HOME", tmp)
	t.Setenv("USERPROFILE", tmp)

	writeConfig(t, tmp, `{"only": {}}`)

	got := AutoDetectProfile()
	if got != "only" {
		t.Errorf("got %q, want %q", got, "only")
	}
}

func TestAutoDetectProfile_MultipleReturnsEmpty(t *testing.T) {
	tmp := t.TempDir()
	t.Setenv("HOME", tmp)
	t.Setenv("USERPROFILE", tmp)

	writeConfig(t, tmp, `{"profiles": {"a": {}, "b": {}}}`)

	got := AutoDetectProfile()
	if got != "" {
		t.Errorf("expected empty, got %q", got)
	}
}

func TestAutoDetectProfile_NoFile(t *testing.T) {
	tmp := t.TempDir()
	t.Setenv("HOME", tmp)
	t.Setenv("USERPROFILE", tmp)

	got := AutoDetectProfile()
	if got != "" {
		t.Errorf("expected empty, got %q", got)
	}
}
