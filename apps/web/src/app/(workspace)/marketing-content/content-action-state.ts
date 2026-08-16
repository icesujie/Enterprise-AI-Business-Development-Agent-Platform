export type ContentActionState = {
  status: "idle" | "success" | "error";
  code?: "stale" | "permission" | "not_found" | "conflict" | "validation";
  message?: string;
};

export const initialContentActionState: ContentActionState = { status: "idle" };
