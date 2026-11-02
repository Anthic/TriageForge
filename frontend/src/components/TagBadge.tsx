import { TAG_CLASSES } from "@/lib/constants";
import type { ResolutionTag } from "@/types";

interface TagBadgeProps {
  tag: ResolutionTag;
}

export function TagBadge({ tag }: TagBadgeProps) {
  return <span className={TAG_CLASSES[tag]}>{tag}</span>;
}
