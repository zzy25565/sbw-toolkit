import org.objectweb.asm.ClassReader;
import org.objectweb.asm.ClassWriter;
import org.objectweb.asm.tree.AbstractInsnNode;
import org.objectweb.asm.tree.ClassNode;
import org.objectweb.asm.tree.FieldInsnNode;
import org.objectweb.asm.tree.InsnList;
import org.objectweb.asm.tree.InvokeDynamicInsnNode;
import org.objectweb.asm.tree.LdcInsnNode;
import org.objectweb.asm.tree.MethodInsnNode;
import org.objectweb.asm.tree.MethodNode;

import java.io.InputStream;
import java.nio.file.Files;
import java.nio.file.Path;
import java.nio.file.Paths;
import java.util.Enumeration;
import java.util.zip.ZipEntry;
import java.util.zip.ZipFile;
import java.util.zip.ZipOutputStream;

/**
 * Removes the Pantsir-S1 vehicle from the ashvehicle mod.
 *
 * Three registration sites are patched (entity / renderer / creative tab) and every
 * pa_pantsir asset plus its recipe is dropped from the jar.
 */
public class PatchAsh {

    public static void main(String[] args) throws Exception {
        Path jar = Paths.get(args[0]);
        Path out = Paths.get(args[1]);

        try (ZipFile zip = new ZipFile(jar.toFile());
             ZipOutputStream zos = new ZipOutputStream(Files.newOutputStream(out))) {

            Enumeration<? extends ZipEntry> en = zip.entries();
            while (en.hasMoreElements()) {
                ZipEntry e = en.nextElement();
                byte[] data;
                try (InputStream in = zip.getInputStream(e)) {
                    data = in.readAllBytes();
                }
                String name = e.getName();

                if (name.contains("pa_pantsir")) {
                    System.out.println("dropped asset: " + name);
                    continue;
                }

                if (name.equals("Aru/Aru/ashvehicle/init/ModEntities.class")) {
                    data = patchEntity(data);
                } else if (name.equals("Aru/Aru/ashvehicle/init/ModEntityRenderers.class")) {
                    data = patchRenderer(data);
                } else if (name.equals("Aru/Aru/ashvehicle/init/ModTabs.class")) {
                    data = patchTab(data);
                }

                ZipEntry ne = new ZipEntry(name);
                ne.setTime(e.getTime());
                zos.putNextEntry(ne);
                zos.write(data);
                zos.closeEntry();
            }
        }
        System.out.println("written: " + out);
    }

    /** removes: ldc "pa_pantsir"; invokedynamic factory; invokestatic tank(...); putstatic PANTSIR_S1 */
    private static byte[] patchEntity(byte[] data) {
        ClassNode cn = new ClassNode();
        new ClassReader(data).accept(cn, 0);
        boolean hit = false;

        for (MethodNode mn : cn.methods) {
            InsnList list = mn.instructions;
            for (AbstractInsnNode node : list.toArray()) {
                if (!(node instanceof LdcInsnNode ldc) || !"pa_pantsir".equals(ldc.cst)) continue;
                AbstractInsnNode a = ldc.getNext();
                AbstractInsnNode b = a == null ? null : a.getNext();
                AbstractInsnNode c = b == null ? null : b.getNext();
                if (b instanceof MethodInsnNode mi && "tank".equals(mi.name)
                        && c instanceof FieldInsnNode fi && "PANTSIR_S1".equals(fi.name)) {
                    list.remove(ldc);
                    list.remove(a);
                    list.remove(b);
                    list.remove(c);
                    hit = true;
                    System.out.println("ModEntities: removed pantsir registration");
                    break;
                }
            }
            if (hit) break;
        }
        if (!hit) throw new IllegalStateException("ModEntities: pantsir pattern not found");
        return write(cn);
    }

    /** removes the whole getstatic PANTSIR_S1 .. registerEntityRenderer(...) range */
    private static byte[] patchRenderer(byte[] data) {
        ClassNode cn = new ClassNode();
        new ClassReader(data).accept(cn, 0);
        boolean hit = false;

        for (MethodNode mn : cn.methods) {
            InsnList list = mn.instructions;
            for (AbstractInsnNode node : list.toArray()) {
                // the renderer itself is hidden in the BootstrapMethods of an
                // invokedynamic, so the only reliable anchor is the entity field
                if (!(node instanceof FieldInsnNode fi)) continue;
                if (!"PANTSIR_S1".equals(fi.name)) continue;

                AbstractInsnNode start = node;
                AbstractInsnNode end = node;
                for (int i = 0; i < 10 && end != null; i++) {
                    if (end instanceof MethodInsnNode mi && "registerEntityRenderer".equals(mi.name)) break;
                    end = end.getNext();
                }
                if (start == null || end == null) continue;

                AbstractInsnNode cur = start;
                while (cur != null) {
                    AbstractInsnNode next = cur.getNext();
                    list.remove(cur);
                    if (cur == end) break;
                    cur = next;
                }
                hit = true;
                System.out.println("ModEntityRenderers: removed pantsir renderer");
                break;
            }
            if (hit) break;
        }
        if (!hit) throw new IllegalStateException("ModEntityRenderers: pantsir pattern not found");
        return write(cn);
    }

    /** removes the whole getstatic PANTSIR_S1 .. Output.accept(...) range */
    private static byte[] patchTab(byte[] data) {
        ClassNode cn = new ClassNode();
        new ClassReader(data).accept(cn, 0);
        boolean hit = false;

        for (MethodNode mn : cn.methods) {
            InsnList list = mn.instructions;
            for (AbstractInsnNode node : list.toArray()) {
                if (!(node instanceof FieldInsnNode fi)) continue;
                if (!"PANTSIR_S1".equals(fi.name)) continue;

                AbstractInsnNode end = node;
                for (int i = 0; i < 12 && end != null; i++) {
                    if (end instanceof MethodInsnNode mi && "accept".equals(mi.name)) break;
                    end = end.getNext();
                }
                if (end == null) continue;

                AbstractInsnNode cur = node;
                while (cur != null) {
                    AbstractInsnNode next = cur.getNext();
                    list.remove(cur);
                    if (cur == end) break;
                    cur = next;
                }
                hit = true;
                System.out.println("ModTabs: removed pantsir tab entry");
                break;
            }
            if (hit) break;
        }
        if (!hit) System.out.println("ModTabs: no PANTSIR_S1 reference (skipped)");
        return write(cn);
    }

    private static boolean referencesPantsir(AbstractInsnNode node) {
        if (node instanceof MethodInsnNode mi) return mi.owner.contains("pantsirS1Renderer");
        if (node instanceof InvokeDynamicInsnNode id) {
            return id.desc.contains("pantsirS1Renderer") || id.name.contains("pantsir");
        }
        return false;
    }

    private static byte[] write(ClassNode cn) {
        ClassWriter cw = new ClassWriter(ClassWriter.COMPUTE_FRAMES);
        cn.accept(cw);
        return cw.toByteArray();
    }
}
