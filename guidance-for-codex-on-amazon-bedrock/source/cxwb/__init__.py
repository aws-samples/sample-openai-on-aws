"""cxwb — guided deploy for Codex on Amazon Bedrock."""

__version__ = "0.1.0"

# Guide-wide recommended default; documented as a pre-launch placeholder
# in docs/reference-regions.md until GPT-5.4 is GA on Bedrock.
DEFAULT_MODEL = "openai.gpt-5.4"

# LiteLLM image versions for automated Docker builds
# See https://github.com/berriai/litellm/pkgs/container/litellm/versions
LITELLM_RECOMMENDED_VERSION = "main-v1.82.3-stable.patch.2"
LITELLM_STABLE_VERSIONS = [
    "main-v1.82.3-stable.patch.2",
    "main-v1.80.5-stable",
    "main-v1.78.0-stable",
    "main-latest",
]
