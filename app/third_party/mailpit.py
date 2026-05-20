import httpx


class MailpitMailer:
    """Sends emails via Mailpit's HTTP send API."""

    def __init__(self, base_url: str) -> None:
        self._base_url = base_url.rstrip("/")

    async def send_activation_code(self, email: str, code: str) -> None:
        async with httpx.AsyncClient() as client:
            await client.post(
                f"{self._base_url}/api/v1/send",
                json={
                    "From": {"Email": "noreply@app.local", "Name": "App"},
                    "To": [{"Email": email}],
                    "Subject": "Your activation code",
                    "Text": f"Your activation code is: {code}",
                },
            )
