"""Package the repository without Git/venv/cache; verify every archived byte."""
import hashlib
import json
from pathlib import Path
import subprocess
import zipfile

def digest(data):return hashlib.sha256(data).hexdigest()

def main():
    root=Path.cwd()
    output=root.parent/'output'
    output.mkdir(exist_ok=True)
    dest=output/'MURL_Chess_Oct14_2026_Review_Package.zip'
    manifest_path=Path('deliverables/october14/manifest.json')
    names=subprocess.check_output(['git','ls-files','-co','--exclude-standard','-z']).decode().split('\0')
    names=sorted({name for name in names if name and name!=manifest_path.as_posix()})
    assert names and not any('.venv/' in n or '__pycache__/' in n or n.startswith('.git/') for n in names)
    manifest={name:dict(bytes=Path(name).stat().st_size,sha256=digest(Path(name).read_bytes())) for name in names}
    manifest_path.write_text(json.dumps(dict(algorithm='SHA-256',scope='All archive payload files except this manifest itself',files=manifest),indent=2))
    with zipfile.ZipFile(dest,'w',zipfile.ZIP_DEFLATED) as z:
        for name in names+[manifest_path.as_posix()]:z.write(name,'murl-chess/'+name)
    with zipfile.ZipFile(dest) as z:
        assert z.testzip() is None
        assert len(z.namelist())==len(names)+1
        for name,meta in manifest.items():
            data=z.read('murl-chess/'+name)
            assert len(data)==meta['bytes'] and digest(data)==meta['sha256'],name
        assert z.read('murl-chess/'+manifest_path.as_posix())==manifest_path.read_bytes()
    result=dict(archive=dest.name,bytes=dest.stat().st_size,sha256=digest(dest.read_bytes()),
                payload_files=len(names)+1,zip_crc_check='passed',all_payload_hashes='passed')
    (output/'package_integrity.json').write_text(json.dumps(result,indent=2))
    print(json.dumps(result,indent=2))

if __name__=='__main__':main()
