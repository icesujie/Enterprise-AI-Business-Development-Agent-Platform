export type PublicContentActionState = {
  status: "idle" | "success" | "error";
  code?: "stale" | "permission" | "not_found" | "conflict" | "validation";
  message?: string;
};

export const initialPublicContentActionState: PublicContentActionState = {
  status: "idle",
};
