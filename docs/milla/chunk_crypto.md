# Milla Custom Chunk Cryptography Module

The `milla/chunk_crypto.py` module manages the custom storage chunk encryption/decryption scheme utilizing Stochastic Proof-of-Work and Statistical Phantom Node tweaks.

## Chunk Layout (4096 Bits)
- **Bits `0..15` ($x$, 16 bits)**: Random iteration count $x$ ($1 \le x \le 65535$).
- **Bits `16..63` ($y$, 48 bits)**: Offset compensation modifier $y = (E - m) \bmod 2^{48}$.
- **Bits `64..4095` ($z_{enc}$, 4032 bits)**: Encrypted payload (3999b) + Anti-Phantom Tweak (1b) + encrypted pointer (32b).

## Encryption Algorithm
1. Pick random 48-bit secret key integer $E \in [1, 2^{48}-1]$.
2. Determine 1-bit Anti-Phantom Tweak: if `sum(payload) + sum(ptr) == 2016`, tweak=1. Otherwise, tweak=0. This mathematically guarantees legitimate chunks never trigger Phantom Node conditions.
3. Encrypt data $z = \text{payload} \mathbin{\Vert} \text{tweak} \mathbin{\Vert} \text{ptr}$ using PRF keystream derived from $E$ via XOR.
4. Pick uniformly random 16-bit iteration depth $x$.
5. Compute Stochastic Proof-of-Work $m = \text{Hash}^x(\text{enc\_z}) \pmod{2^{48}}$.
6. Compute $y = (E - m) \bmod 2^{48}$.
7. Chunk $= x \mathbin{\Vert} y \mathbin{\Vert} \text{enc\_z}$.

## Decryption Algorithm
1. Extract $x$ (16b), $y$ (48b), and $\text{enc\_z}$ (4032b).
2. Compute Stochastic Proof-of-Work $m = \text{Hash}^x(\text{enc\_z}) \pmod{2^{48}}$.
3. Reconstruct secret key $E = (m + y) \bmod 2^{48}$.
4. Expand $E$ into keystream and XOR decrypt $\text{enc\_z}$ to recover $\text{payload}$ (3999b), $\text{tweak}$ (1b), and $\text{ptr}$ (32b).
