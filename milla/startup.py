'''
THIS FILE IS LINKED TO POS. (not for now...)

Main system for startup procedures.
'''

import hashlib
import json
import os
import secrets
import shutil


class MillaEnvironment:
    """
    Manages the volatile runtime environment for a Milla volume.
    Creates a temporary directory alongside the .pos file to hold the decrypted copy and the runtime config.json.
    """
    def __init__(self, pos_file_path: str):
        if not os.path.exists(pos_file_path):
            raise FileNotFoundError(f"POS file not found: {pos_file_path}")
            
        self.original_pos_path = os.path.abspath(pos_file_path)
        self.pos_dir = os.path.dirname(self.original_pos_path)
        self.pos_filename = os.path.basename(self.original_pos_path)
        
        self.session_id = secrets.token_hex(4)
        
        self.temp_dir_name = f".temp-{self.pos_filename}-{self.session_id}"
        self.temp_dir = os.path.join(self.pos_dir, self.temp_dir_name)
        
        self.decrypted_pos_path = os.path.join(self.temp_dir, f"decrypted-{self.pos_filename}")
        self.config_path = os.path.join(self.temp_dir, "config.json")
        self.mounted = False

    def mount(self):
        os.makedirs(self.temp_dir, exist_ok=True)
        # For now, just copy since monolith encryption isn't implemented
        _ = shutil.copy2(self.original_pos_path, self.decrypted_pos_path)
        
        config_data = {"source_file": self.original_pos_path}
        with open(self.config_path, "w") as f:
            json.dump(config_data, f, indent=4)
            
        self.mounted = True
        return self

    def unmount(self):
        if not self.mounted:
            return
            
        if os.path.exists(self.decrypted_pos_path):
            try:
                size = os.path.getsize(self.decrypted_pos_path)
                with open(self.decrypted_pos_path, "r+b") as f:
                    _ = f.write(b'\x00' * size)
                    f.flush()
                    os.fsync(f.fileno())
                os.remove(self.decrypted_pos_path)
            except OSError:
                pass
                
        if os.path.exists(self.config_path):
            try:
                os.remove(self.config_path)
            except OSError:
                pass
                
        if os.path.exists(self.temp_dir):
            try:
                shutil.rmtree(self.temp_dir)
            except OSError:
                pass
                
        self.mounted = False

    def __enter__(self):
        return self.mount()

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.unmount()


def derive_outer_key(passphrase: str, total_chunks: int) -> bytes:
    if total_chunks <= 0:
        raise ValueError("total_chunks cannot be negative")

    dynamic_salt = b"Milla Jovovich" + total_chunks.to_bytes(8, 'big')

    return hashlib.scrypt(
        passphrase.encode('utf-8'),
        salt=dynamic_salt,
        n=16384,
        r=8,
        p=1,
        dklen=32
    )

def get_root_chunk_and_fingerprint(passphrase: str, total_chunks: int, word_count: int = 4) -> tuple[int, str]:
    '''
    Function to get the start root chunk, and the verifier fingerprint, from the password.
    '''

    verification_words: list[str] = ['alfa', 'bravo', 'charlie', 'delta', 'echo', 'foxtrot', 'golf', 'hotel', 'india', 'juliett', 'kilo', 'lima', 'mike', 'november', 'oscar', 'papa', 'quebec', 'romeo', 'sierra', 'tango', 'uniform', 'victor', 'whiskey', 'xray', 'yankee', 'zulu']

    derived_bytes = derive_outer_key(passphrase, total_chunks)

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


