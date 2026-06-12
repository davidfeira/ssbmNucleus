"""Dump every material TOBJ image from a costume DAT (datprobe only dumps
matanim frames) and report texture-less DOBJs with their material diffuse
colors — hunting for parts (e.g. Pikachu/Pichu cheeks) that are pure material
color and therefore invisible to texture recolors."""
import struct
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'backend'))
from skinlab.datprobe import DatFile, decode_image, save_png


def main(dat_path, out_dir):
    dat = DatFile(dat_path)
    out = Path(out_dir)
    out.mkdir(parents=True, exist_ok=True)
    roots = dat.find_roots('_joint')
    share = [(n, o) for n, o in roots
             if n.endswith('_Share_joint') or (n.endswith('_joint')
                                               and 'matanim' not in n)]
    print(f'{Path(dat_path).name} roots: {[n for n, _ in roots]}')
    for name, root in share:
        if 'matanim' in name:
            continue
        # textured DOBJs
        infos = dat.jobj_textures(root)
        print(f'{name}: {len(infos)} material TOBJ images')
        for k, t in enumerate(infos):
            rows = decode_image(t.image, t.tlut)
            save_png(rows, out / f'tex{k:02d}_j{t.jobj_index}d{t.dobj_index}_'
                                 f'{t.image.width}x{t.image.height}.png')
        # texture-less DOBJs: walk like jobj_textures but report material color
        jobjs = dat._iter_tree(root, 0x08, 0x0C)
        print('--- DOBJs without textures (material color only) ---')
        for j_idx, j in enumerate(jobjs):
            flags = dat.u32(j + 0x04)
            if flags & (1 << 14) or flags & (1 << 29):
                continue
            dobj = dat.ptr(j + 0x10)
            d_idx = 0
            while dobj is not None:
                mobj = dat.ptr(dobj + 0x08)
                if mobj is not None:
                    tobj = dat.ptr(mobj + 0x08)
                    mat = dat.ptr(mobj + 0x0C)
                    if tobj is None and mat is not None:
                        amb = struct.unpack_from('>4B', dat.data, mat + 0x00)
                        dif = struct.unpack_from('>4B', dat.data, mat + 0x04)
                        print(f'  jobj {j_idx} dobj {d_idx}: ambient={amb} '
                              f'diffuse={dif}')
                dobj = dat.ptr(dobj + 0x04)
                d_idx += 1


if __name__ == '__main__':
    main(sys.argv[1], sys.argv[2])
