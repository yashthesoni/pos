"""
LINKED TO POS
Manages MillaObject chain assembly and folder hierarchies.
Uses existing driver, pointer, and cryptographic functions.
"""

from milla.chunk_crypto import decrypt_chunk, verify_phantom
from milla.constants import PAYLOAD_BYTES
from milla.driver import MillaDriver
from milla.pointer import decode_address, encode_address
from milla.startup import get_root_chunk_and_fingerprint
from posetem.pos import POS


class MillaObject:
    """
    A complete Milla object built by traversing chunks from a starting position.

    Attributes:
        content: One bytes object with the entire decrypted content (non-phantom).
        chunks: One tuple with the positions of chunks in order of appearance.
        phantom_chunks: One tuple with the positions of phantom chunks.
    """

    def __init__(self, driver: MillaDriver | POS, start_chunk: int, max_budget: int = 1000):
        if isinstance(driver, POS):
            driver = MillaDriver(driver)

        chunks_list: list[int] = []
        phantoms_list: list[int] = []
        content_parts: list[bytes] = []
        visited: set[int] = set()

        current_idx = start_chunk
        steps = 0

        while current_idx and current_idx not in visited:
            if current_idx < 1 or current_idx > driver.total_chunks:
                break
            if steps >= max_budget:
                break

            visited.add(current_idx)
            chunks_list.append(current_idx)
            steps += 1

            # Read and decrypt using existing functions
            raw_chunk = driver.read_chunk(current_idx)
            payload, ptr = decrypt_chunk(raw_chunk)

            # Check for phantom using chunk_crypto verification
            if verify_phantom(payload):
                phantoms_list.append(current_idx)
            else:
                content_parts.append(payload)

            # Move to the next chunk using existing decode_address function
            current_idx = decode_address(ptr, driver.total_chunks)

        self.content: bytes = b"".join(content_parts)
        self.chunks: tuple[int, ...] = tuple(chunks_list)
        self.phantom_chunks: tuple[int, ...] = tuple(phantoms_list)

    def __bytes__(self) -> bytes:
        return self.content

    def __len__(self) -> int:
        return len(self.content)

    def __repr__(self) -> str:
        return (
            f"<MillaObject size={len(self.content)}B, "
            f"chunks={self.chunks}, phantoms={self.phantom_chunks}>"
        )


def pack_folder(child_chunks: list[int], total_chunks: int, name: str = "") -> bytes:
    """
    Pack a folder payload (500 bytes) containing child chunk pointers.
    - If name is empty or '/': packs root folder (up to 125 pointer slots).
    - If name is given: packs subfolder (1B marker + 64B name + up to 108 pointer slots).
    """
    is_root = not name or name == "/"
    capacity = 125 if is_root else 108
    slots: list[bytes] = []

    for c in child_chunks[:capacity]:
        slots.append(encode_address(c, total_chunks))

    while len(slots) < capacity:
        if child_chunks:
            slots.append(encode_address(child_chunks[len(slots) % len(child_chunks)], total_chunks))
        else:
            slots.append(encode_address(0, total_chunks))

    ptrs_bytes = b"".join(slots)

    if is_root:
        return ptrs_bytes.ljust(PAYLOAD_BYTES, b"\x00")[:PAYLOAD_BYTES]
    else:
        header = b"\x01" + name.encode("ascii", errors="replace")[:64].ljust(64, b"\x00")
        return (header + ptrs_bytes).ljust(PAYLOAD_BYTES, b"\x00")[:PAYLOAD_BYTES]


def unpack_folder(payload: bytes, total_chunks: int, is_root: bool = False) -> tuple[bool, str, list[int]]:
    """
    Checks if a payload is a folder and recovers (is_folder, name, child_chunk_indices).
    """
    if len(payload) != PAYLOAD_BYTES:
        return False, "", []

    if is_root:
        children: list[int] = []
        seen: set[int] = set()
        for i in range(125):
            slot = payload[i * 4 : (i + 1) * 4]
            c = decode_address(slot, total_chunks)
            if c > 0 and c not in seen:
                seen.add(c)
                children.append(c)
        return True, "/", children

    if payload[0] == 1:
        raw_name = payload[1:65].split(b"\x00", 1)[0]
        try:
            name = raw_name.decode("ascii")
            children = []
            seen = set()
            for i in range(108):
                slot = payload[65 + i * 4 : 65 + (i + 1) * 4]
                c = decode_address(slot, total_chunks)
                if c > 0 and c not in seen:
                    seen.add(c)
                    children.append(c)
            return True, name, children
        except UnicodeDecodeError:
            pass

    return False, "", []


class MillaFolder:
    """Represents a folder node containing children (subfolders and MillaObjects)."""

    def __init__(self, name: str = "/", chunk: int = 0):
        self.name: str = name
        self.chunk: int = chunk
        self.children: list[MillaFolder | MillaObject] = []

    def add_child(self, child: "MillaFolder | MillaObject") -> None:
        self.children.append(child)

    def get_child(self, name: str) -> "MillaFolder | None":
        for child in self.children:
            if isinstance(child, MillaFolder) and child.name == name:
                return child
        return None

    def __repr__(self) -> str:
        return f"<MillaFolder name={self.name!r} chunk={self.chunk} children={len(self.children)}>"


class MillaTree:
    """
    Volatile tree builder for Milla.
    Mounts using passphrase and constructs MillaFolders and MillaObjects.
    """

    def __init__(self, driver_or_pos: MillaDriver | POS, total_chunks: int | None = None):
        if isinstance(driver_or_pos, POS):
            self.driver = MillaDriver(driver_or_pos)
            self.total_chunks = self.driver.total_chunks
        else:
            self.driver = driver_or_pos
            self.total_chunks = total_chunks or self.driver.total_chunks

        self.root: MillaFolder | None = None
        self.visited: set[int] = set()

    def get_object(self, start_chunk: int) -> MillaObject:
        """Create a complete MillaObject starting from a given chunk."""
        return MillaObject(self.driver, start_chunk)

    def build_tree(self, passphrase: str) -> MillaFolder:
        """Mounts the volume using passphrase and builds the in-RAM folder tree."""
        root_idx, _ = get_root_chunk_and_fingerprint(passphrase, self.total_chunks)
        self.visited = set()
        self.root = self._discover_folder(root_idx, name="/", is_root=True)
        return self.root

    def _discover_folder(self, chunk_idx: int, name: str, is_root: bool = False) -> MillaFolder:
        folder = MillaFolder(name=name, chunk=chunk_idx)
        if chunk_idx in self.visited or chunk_idx < 1 or chunk_idx > self.total_chunks:
            return folder

        self.visited.add(chunk_idx)

        raw = self.driver.read_chunk(chunk_idx)
        payload, _ = decrypt_chunk(raw)
        if verify_phantom(payload):
            return folder

        is_dir, folder_name, child_chunks = unpack_folder(payload, self.total_chunks, is_root=is_root)
        if folder_name and not is_root:
            folder.name = folder_name

        for child_idx in child_chunks:
            if child_idx in self.visited or child_idx < 1 or child_idx > self.total_chunks:
                continue

            child_raw = self.driver.read_chunk(child_idx)
            child_payload, _ = decrypt_chunk(child_raw)
            is_sub = False
            sub_name = ""
            if not verify_phantom(child_payload):
                is_sub, sub_name, _ = unpack_folder(child_payload, self.total_chunks, is_root=False)

            if is_sub:
                subfolder = self._discover_folder(child_idx, name=sub_name or f"folder_{child_idx}", is_root=False)
                folder.add_child(subfolder)
            else:
                obj = MillaObject(self.driver, child_idx)
                folder.add_child(obj)

        return folder

    def locate_path(self, path: str) -> MillaFolder | None:
        """Traverse the built tree and locate a folder by path."""
        if not self.root:
            return None
        if path == "/":
            return self.root

        parts = [p for p in path.split("/") if p]
        current: MillaFolder = self.root

        for part in parts:
            next_folder = current.get_child(part)
            if not next_folder:
                return None
            current = next_folder

        return current

    def print_tree(
        self,
        node: MillaFolder | None = None,
        prefix: str = "",
        is_last: bool = True,
        is_root: bool = True,
    ) -> str:
        """Renders an ASCII visualization of the tree."""
        if node is None:
            node = self.root
        if node is None:
            return "<Empty Tree>"

        lines: list[str] = []
        if is_root:
            lines.append(f"{node.name} (chunk: {node.chunk})")
            child_prefix = ""
        else:
            connector = "└── " if is_last else "├── "
            lines.append(f"{prefix}{connector}{node.name} (chunk: {node.chunk})")
            child_prefix = prefix + ("    " if is_last else "│   ")

        for idx, child in enumerate(node.children):
            last = idx == len(node.children) - 1
            if isinstance(child, MillaFolder):
                lines.append(self.print_tree(child, prefix=child_prefix, is_last=last, is_root=False))
            else:
                conn = "└── " if last else "├── "
                lines.append(f"{child_prefix}{conn}<MillaObject chunks={child.chunks} size={len(child.content)}B>")

        return "\n".join(lines)
