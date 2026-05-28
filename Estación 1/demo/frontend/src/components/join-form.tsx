"use client";

import { useCallback, useMemo, useRef, useState } from "react";
import { Camera, Loader2 } from "lucide-react";
import {
  SESSION_CODE,
  getUploadUrl,
  joinSession,
  uploadToS3
} from "@/lib/api";
import { setRegistration } from "@/lib/storage";
import { MAX_SKILLS, MIN_SKILLS, SKILLS_CATALOG } from "@/constants/skills";
import { cn } from "@/lib/utils";
import { SkillChip } from "./skill-chip";

interface JoinFormProps {
  readonly onJoined: () => void;
}

const ACCEPTED_TYPES = ["image/jpeg", "image/png", "image/webp"];
const MAX_PHOTO_BYTES = 2 * 1024 * 1024;

export function JoinForm({ onJoined }: JoinFormProps) {
  const [displayName, setDisplayName] = useState("");
  const [selectedSkills, setSelectedSkills] = useState<Set<string>>(new Set());
  const [photo, setPhoto] = useState<File | null>(null);
  const [photoPreview, setPhotoPreview] = useState<string | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const fileInputRef = useRef<HTMLInputElement>(null);

  const isAtCap = selectedSkills.size >= MAX_SKILLS;

  const toggleSkill = useCallback((skillId: string) => {
    setSelectedSkills((prev) => {
      const next = new Set(prev);
      if (next.has(skillId)) {
        next.delete(skillId);
      } else if (next.size < MAX_SKILLS) {
        next.add(skillId);
      }
      return next;
    });
  }, []);

  const onPhotoSelected = useCallback((e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (!file) return;
    if (!ACCEPTED_TYPES.includes(file.type)) {
      setError("Solo JPEG, PNG o WebP");
      return;
    }
    if (file.size > MAX_PHOTO_BYTES) {
      setError("Foto máximo 2MB");
      return;
    }
    setError(null);
    setPhoto(file);
    setPhotoPreview(URL.createObjectURL(file));
  }, []);

  const submit = useCallback(
    async (e: React.FormEvent) => {
      e.preventDefault();
      const trimmedName = displayName.trim();
      if (!trimmedName) {
        setError("Ingresa tu nombre");
        return;
      }
      if (selectedSkills.size < MIN_SKILLS) {
        setError(`Selecciona al menos ${MIN_SKILLS} skills`);
        return;
      }

      setError(null);
      setLoading(true);
      try {
        let photoObjectKey = "";
        if (photo) {
          const { uploadUrl, objectKey } = await getUploadUrl({
            sessionCode: SESSION_CODE,
            contentType: photo.type
          });
          await uploadToS3(uploadUrl, photo);
          photoObjectKey = objectKey;
        }
        const res = await joinSession({
          sessionCode: SESSION_CODE,
          displayName: trimmedName,
          skills: Array.from(selectedSkills),
          photoObjectKey
        });
        setRegistration(res.participantId, SESSION_CODE);
        onJoined();
      } catch (err) {
        setError(err instanceof Error ? err.message : "Error al unirse");
      } finally {
        setLoading(false);
      }
    },
    [displayName, selectedSkills, photo, onJoined]
  );

  const skillButtons = useMemo(
    () =>
      SKILLS_CATALOG.map((s) => {
        const selected = selectedSkills.has(s.skillId);
        return (
          <SkillChip
            key={s.skillId}
            mode="select"
            skillId={s.skillId}
            skillName={s.skillName}
            selected={selected}
            disabled={!selected && isAtCap}
            onClick={() => toggleSkill(s.skillId)}
          />
        );
      }),
    [selectedSkills, isAtCap, toggleSkill]
  );

  return (
    <form onSubmit={submit} className="space-y-5">
      <div>
        <label className="block text-sm font-medium mb-1.5">Nombre</label>
        <input
          type="text"
          data-testid="join-form-display-name"
          value={displayName}
          onChange={(e) => setDisplayName(e.target.value)}
          maxLength={200}
          className="w-full px-3 py-2 rounded-lg border border-[var(--color-border)] bg-[var(--color-card)] text-[var(--color-foreground)] focus:outline-none focus:border-[var(--color-primary)]"
          placeholder="Tu nombre"
        />
      </div>

      <div>
        <label className="block text-sm font-medium mb-1.5">
          Skills (3–5)
          <span className="ml-2 text-xs text-[var(--color-muted-foreground)]">
            {selectedSkills.size}/{MAX_SKILLS}
          </span>
        </label>
        <div className="flex flex-wrap gap-2">{skillButtons}</div>
      </div>

      <div>
        <label className="block text-sm font-medium mb-1.5">Foto (opcional)</label>
        <input
          ref={fileInputRef}
          type="file"
          accept="image/jpeg,image/png,image/webp"
          onChange={onPhotoSelected}
          className="hidden"
        />
        <button
          type="button"
          data-testid="join-form-photo-button"
          onClick={() => fileInputRef.current?.click()}
          className="inline-flex items-center gap-2 px-3 py-2 rounded-lg border border-[var(--color-border)] bg-[var(--color-card)] hover:border-[var(--color-primary)] transition-colors"
        >
          <Camera className="h-4 w-4" />
          {photo ? "Cambiar foto" : "Subir foto"}
        </button>
        {photoPreview && (
          <img
            src={photoPreview}
            alt="Preview"
            className="mt-2 h-20 w-20 rounded-full object-cover"
          />
        )}
      </div>

      <p className="text-xs text-[var(--color-muted-foreground)]">
        No subas información sensible; contenido puede ser removido.
      </p>

      {error && (
        <p
          data-testid="join-form-error"
          className="text-sm text-[var(--color-danger)]"
        >
          {error}
        </p>
      )}

      <button
        type="submit"
        data-testid="join-form-submit"
        disabled={loading}
        className={cn(
          "w-full py-2.5 rounded-lg font-semibold transition-colors",
          "bg-[var(--color-primary)] text-[var(--color-primary-foreground)]",
          "hover:opacity-90",
          loading && "opacity-60 cursor-not-allowed"
        )}
      >
        {loading ? (
          <span className="inline-flex items-center gap-2 justify-center">
            <Loader2 className="h-4 w-4 animate-spin" />
            Uniendo…
          </span>
        ) : (
          "Unirme"
        )}
      </button>
    </form>
  );
}
