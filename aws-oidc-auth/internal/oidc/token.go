package oidc

import (
	"encoding/json"
	"fmt"
	"io"
	"net/http"
	"net/url"
	"strings"
	"time"
)

// TokenResponse holds the OIDC token endpoint response.
type TokenResponse struct {
	IDToken      string `json:"id_token"`
	AccessToken  string `json:"access_token"`
	RefreshToken string `json:"refresh_token"`
	TokenType    string `json:"token_type"`
	ExpiresIn    int    `json:"expires_in"`
}

// TokenExchangeError captures a non-success token endpoint response.
type TokenExchangeError struct {
	Operation  string
	StatusCode int
	Body       string
}

func (e *TokenExchangeError) Error() string {
	return fmt.Sprintf("%s failed (HTTP %d): %s", e.Operation, e.StatusCode, e.Body)
}

// IsInvalidGrant reports whether the provider explicitly rejected the refresh token.
func (e *TokenExchangeError) IsInvalidGrant() bool {
	if e == nil {
		return false
	}
	if e.StatusCode != http.StatusBadRequest && e.StatusCode != http.StatusUnauthorized {
		return false
	}

	var payload struct {
		Error string `json:"error"`
	}
	if err := json.Unmarshal([]byte(e.Body), &payload); err == nil && payload.Error != "" {
		return payload.Error == "invalid_grant"
	}

	return strings.Contains(strings.ToLower(e.Body), "invalid_grant")
}

// ConfidentialClientOpts holds optional parameters for confidential client authentication.
type ConfidentialClientOpts struct {
	ClientAssertion     string
	ClientAssertionType string
	ClientSecret        string
}

func applyConfidentialClientOpts(data url.Values, opts *ConfidentialClientOpts) {
	if opts == nil {
		return
	}
	if opts.ClientAssertion != "" {
		data.Set("client_assertion", opts.ClientAssertion)
		data.Set("client_assertion_type", opts.ClientAssertionType)
		return
	}
	if opts.ClientSecret != "" {
		data.Set("client_secret", opts.ClientSecret)
	}
}

// ExchangeCode exchanges an authorization code for tokens at the provider's token endpoint.
func ExchangeCode(tokenURL, code, redirectURI, clientID, codeVerifier string) (*TokenResponse, error) {
	return ExchangeCodeWithOpts(tokenURL, code, redirectURI, clientID, codeVerifier, nil)
}

// ExchangeCodeWithOpts exchanges an authorization code with optional confidential client parameters.
func ExchangeCodeWithOpts(tokenURL, code, redirectURI, clientID, codeVerifier string, opts *ConfidentialClientOpts) (*TokenResponse, error) {
	data := url.Values{
		"grant_type":    {"authorization_code"},
		"code":          {code},
		"redirect_uri":  {redirectURI},
		"client_id":     {clientID},
		"code_verifier": {codeVerifier},
	}
	applyConfidentialClientOpts(data, opts)

	client := &http.Client{Timeout: 30 * time.Second}
	resp, err := client.Post(tokenURL, "application/x-www-form-urlencoded", strings.NewReader(data.Encode()))
	if err != nil {
		return nil, fmt.Errorf("token request failed: %w", err)
	}
	defer resp.Body.Close()

	body, err := io.ReadAll(resp.Body)
	if err != nil {
		return nil, fmt.Errorf("reading token response: %w", err)
	}

	if resp.StatusCode != http.StatusOK {
		return nil, &TokenExchangeError{
			Operation:  "token exchange",
			StatusCode: resp.StatusCode,
			Body:       string(body),
		}
	}

	var tokenResp TokenResponse
	if err := json.Unmarshal(body, &tokenResp); err != nil {
		return nil, fmt.Errorf("parsing token response: %w", err)
	}

	return &tokenResp, nil
}

// RefreshTokenExchange exchanges a refresh_token for fresh tokens at the provider's token endpoint.
func RefreshTokenExchange(tokenURL, refreshToken, clientID string) (*TokenResponse, error) {
	return RefreshTokenExchangeWithOpts(tokenURL, refreshToken, clientID, nil)
}

// RefreshTokenExchangeWithOpts exchanges a refresh_token with optional confidential client parameters.
func RefreshTokenExchangeWithOpts(tokenURL, refreshToken, clientID string, opts *ConfidentialClientOpts) (*TokenResponse, error) {
	data := url.Values{
		"grant_type":    {"refresh_token"},
		"refresh_token": {refreshToken},
		"client_id":     {clientID},
	}
	applyConfidentialClientOpts(data, opts)

	client := &http.Client{Timeout: 30 * time.Second}
	resp, err := client.Post(tokenURL, "application/x-www-form-urlencoded", strings.NewReader(data.Encode()))
	if err != nil {
		return nil, fmt.Errorf("refresh token request failed: %w", err)
	}
	defer resp.Body.Close()

	body, err := io.ReadAll(resp.Body)
	if err != nil {
		return nil, fmt.Errorf("reading refresh token response: %w", err)
	}

	if resp.StatusCode != http.StatusOK {
		return nil, &TokenExchangeError{
			Operation:  "refresh token exchange",
			StatusCode: resp.StatusCode,
			Body:       string(body),
		}
	}

	var tokenResp TokenResponse
	if err := json.Unmarshal(body, &tokenResp); err != nil {
		return nil, fmt.Errorf("parsing refresh token response: %w", err)
	}

	return &tokenResp, nil
}
