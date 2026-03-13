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
                system=system_prompt,
                messages=[{"role": "user", "content": user_message}],
            ) as stream:
                response = stream.get_final_message()

            usage = response.usage
            print(
                f"[Anthropic] Tokens used — input: {usage.input_tokens}, "
                f"output: {usage.output_tokens} | "
                f"Est. cost: ${(usage.input_tokens * 3 + usage.output_tokens * 15) / 1_000_000:.4f}"
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
