# Architectural Notes: 4096-bit Chaff-Based Storage Layout

This document details the low-level bit specifications and cryptographic pipeline for the deniable storage engine built on top of the `pos` shared-memory simulation bus.

## 1. Storage Capacity and Block Size Strategy
* **Chunk Size**: 4096 bits (512 bytes) per block.
* **Addressing System**: 32-bit pointer architecture.

## 2. Chunk Bit Layout
Each 4096-bit block is strictly partitioned at the bit level to preserve structural uniformity, keeping the next-chunk pointer at the terminal end:

| Bit Range | Field Size | Field Purpose |
| :--- | :--- | :--- |
| `0 – 15` | 16 bits | Hash Iteration Depth ($n$), where $1 \le n \le 2^{16}-1$ |
| `16 – 63` | 48 bits | Pseudo-key Modifier / Salt ($A$) |
| `64 – 4063` | 4000 bits | Encrypted Data Payload |
| `4064 – 4095` | 32 bits | Next-Chunk Pointer (encrypted terminal pointer) |

## 3. Cryptographic Pipeline (Key Modifier Generation)

To prevent structural signatures across the drive, each block features an independent, forward-secure key derivation loop.

### Block Encoding (Writing Data)
1. Generate a random **48-bit Block Key**.
2. Pass the core key through the hashing function $n$ times and truncate/clip the output to 48 bits, yielding $H_n$.
3. Compute the stored modifier $A$ via a reversible XOR operation:
   $$A = \text{Key} \oplus H_n$$
4. Write $A$ to the chunk header.

### Block Decoding (Reading Data)
* **Legitimate User**: Decrypts with the correct passphrase to derive the true $H_n$. Recovers the block key via $\text{Key} = A \oplus H_n$, smoothly resolving the trailing next-chunk pointer. 
* **Adversary**: Decrypts with an incorrect passphrase, yielding an invalid $H_n$. The mathematical XOR still succeeds but outputs a garbage 48-bit key. The subsequent data and trailing pointer decrypt into uniform noise.

## 4. Path Deception Mechanics

### Modulo-Wrapped Pointer Mapping
To neutralize adversarial brute-force scripts trying to weed out incorrect passwords using out-of-bounds errors, the terminal 32-bit pointer is wrapped through a modulo function relative to the file system bounds:
$$\text{Target Chunk} = a \pmod b$$
* **$a$**: The raw, decrypted 32-bit integer parsed from the terminal pointer field.
* **$b$**: The total number of blocks allocated in the active `.pos` medium.

**Security Implication**: Every possible decryption outcome maps perfectly to a valid coordinate. The adversary's script is successfully trapped into an endless, randomized path traversal over valid storage chunks without realizing the data is decoy chaff.