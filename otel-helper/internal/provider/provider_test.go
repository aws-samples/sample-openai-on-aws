package provider

import "testing"

func TestDetect(t *testing.T) {
	tests := []struct {
		domain   string
		expected string
	}{
		{"dev-12345.okta.com", "okta"},
		{"myorg.okta.com", "okta"},
		{"myorg.auth0.com", "auth0"},
		{"login.microsoftonline.com", "azure"},
		{"login.microsoftonline.com/tenantid", "azure"},
		{"sts.windows.net", "azure"},
		{"myapp.auth.us-east-1.amazoncognito.com", "cognito"},
		{"cognito-idp.us-east-1.amazonaws.com/us-east-1_abc123", "cognito"},
		{"example.com", "oidc"},
		{"", "oidc"},
	}

	for _, tt := range tests {
		t.Run(tt.domain, func(t *testing.T) {
			result := Detect(tt.domain)
			if result != tt.expected {
				t.Errorf("Detect(%q) = %q, want %q", tt.domain, result, tt.expected)
			}
		})
	}
}
