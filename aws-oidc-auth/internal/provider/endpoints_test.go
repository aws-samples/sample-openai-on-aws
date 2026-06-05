package provider

import "testing"

func TestIsKnown(t *testing.T) {
	known := []string{"okta", "auth0", "azure", "cognito"}
	for _, p := range known {
		if !IsKnown(p) {
			t.Errorf("IsKnown(%q) = false, want true", p)
		}
	}
	if IsKnown("unknown") {
		t.Error("IsKnown(unknown) = true, want false")
	}
	if IsKnown("") {
		t.Error("IsKnown('') = true, want false")
	}
}

func TestConfigs_AllKnownHaveEndpoints(t *testing.T) {
	for name, cfg := range Configs {
		if cfg.AuthorizeEndpoint == "" {
			t.Errorf("provider %q missing AuthorizeEndpoint", name)
		}
		if cfg.TokenEndpoint == "" {
			t.Errorf("provider %q missing TokenEndpoint", name)
		}
		if cfg.Scopes == "" {
			t.Errorf("provider %q missing Scopes", name)
		}
	}
}
