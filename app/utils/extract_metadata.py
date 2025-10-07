from email import message
import re


def extract_text_from_email(msg: message.Message) -> str:
    # Walk email parts to extract text/plain or fallback to html
    text = []
    if msg.is_multipart():
        for part in msg.walk():
            ctype = part.get_content_type()
            disp = str(part.get('Content-Disposition'))
            if ctype == 'text/plain' and 'attachment' not in disp:
                payload = part.get_payload(decode=True)
                if payload:
                    try:
                        text.append(payload.decode(part.get_content_charset() or 'utf-8', errors='ignore'))
                    except Exception:
                        text.append(payload.decode('utf-8', errors='ignore'))
    else:
        payload = msg.get_payload(decode=True)
        if payload:
            try:
                text.append(payload.decode(msg.get_content_charset() or 'utf-8', errors='ignore'))
            except Exception:
                text.append(payload.decode('utf-8', errors='ignore'))

    body = '\n'.join(text).strip()
    if not body:
        # fallback - try to get from html by stripping tags
        html = msg.get_payload(decode=True)
        if html:
            s = html.decode('utf-8', errors='ignore')
            body = re.sub('<[^<]+?>', '', s)
    return body
