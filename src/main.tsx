import { StrictMode } from "react";
import { createRoot } from "react-dom/client";
import { App } from "@/App";
import "@/index.css";

const rootElement = document.getElementById("root");

// `noUncheckedIndexedAccess` and `strict` make this null check mandatory.
// That is the tsconfig earning its keep on line one of the app.
if (!rootElement) {
  throw new Error("Root element #root was not found in index.html");
}

createRoot(rootElement).render(
  <StrictMode>
    <App />
  </StrictMode>,
);
