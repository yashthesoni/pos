'''
INDEPENDENT FILE.
THIS FILE IS NOT LINKED TO POS. (for now)

Main system for startup procedures.
'''

import hashlib


def get_root_chunk_and_fingerprint(passphrase: str, total_chunks: int, word_count: int = 4) -> tuple[int, str]:

    verification_words: list[str] = ['alfa', 'bravo', 'charlie', 'delta', 'echo', 'foxtrot', 'golf', 'hotel', 'india', 'juliett', 'kilo', 'lima', 'mike', 'november', 'oscar', 'papa', 'quebec', 'romeo', 'sierra', 'tango', 'uniform', 'victor', 'whiskey', 'xray', 'yankee', 'zulu']

    if total_chunks <= 0:
        raise ValueError("total_chunks cannot be negative")

    dynamic_salt = b"Milla Jovovich" + total_chunks.to_bytes(8, 'big')

    derived_bytes = hashlib.scrypt(
        passphrase.encode('utf-8'),
        salt=dynamic_salt,
        n=16384,
        r=8,
        p=1,
        dklen=32
    )

    lcn = int.from_bytes(derived_bytes[:16], 'big')
    res = lcn % total_chunks
    root_chunk = total_chunks if res == 0 else res

    fingerprint_val = int.from_bytes(derived_bytes[16:], 'big')

    fingerprint_words: list[str] = []
    for _ in range(word_count):
        word_idx = fingerprint_val % len(verification_words)
        fingerprint_words.append(verification_words[word_idx])
        fingerprint_val //= len(verification_words)

    visual_phrase = " ".join(fingerprint_words)

    return root_chunk, visual_phrase


