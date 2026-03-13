import os
import time
import anthropic

MODEL = "claude-sonnet-4-6"
MAX_TOKENS = 1500


def get_coaching_brief(system_prompt: str, user_message: str) -> str:
    client = anthropic.Anthropic(api_key=os.environ["ANTHROPIC_API_KEY"])

    for attempt in range(3):
        try:
            with client.messages.stream(
                model=MODEL,
                max_tokens=MAX_TOKENS,
                system=[{
                    "type": "text",
                    "text": system_prompt,
                    "cache_control": {"type": "ephemeral"},
                }],
                messages=[{"role": "user", "content": user_message}],
            ) as stream:
                response = stream.get_final_message()

            usage = response.usage
            cache_write = getattr(usage, "cache_creation_input_tokens", 0) or 0
            cache_read = getattr(usage, "cache_read_input_tokens", 0) or 0
            # Sonnet 4.6 pricing: $3/1M input, $15/1M output, $3.75/1M cache write, $0.30/1M cache read
            cost = (
                usage.input_tokens * 3
                + usage.output_tokens * 15
                + cache_write * 3.75
                + cache_read * 0.30
            ) / 1_000_000
            cache_status = f"cache_write={cache_write}, cache_read={cache_read}" if (cache_write or cache_read) else "no cache"
            print(
                f"[Anthropic] Tokens — input: {usage.input_tokens}, output: {usage.output_tokens}, "
                f"{cache_status} | Est. cost: ${cost:.4f}"
            )

            text_blocks = [b.text for b in response.content if b.type == "text"]
            return "\n".join(text_blocks)

        except anthropic.RateLimitError:
            wait = 60 * (attempt + 1)
            print(f"[Anthropic] Rate limited. Waiting {wait}s before retry {attempt + 1}/3...")
            time.sleep(wait)

        except anthropic.APIError as e:
            if attempt == 2:
                raise
            print(f"[Anthropic] API error on attempt {attempt + 1}: {e}. Retrying...")
            time.sleep(5)

    raise RuntimeError("Failed to get coaching brief after 3 attempts.")
