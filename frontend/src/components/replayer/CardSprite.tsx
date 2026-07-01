import spriteMarkup from "@/assets/cards-sprite.svg?raw";

// Injects the card <symbol> sprite into the DOM once so <use href="#card-Xy">
// works anywhere. Render near the app root.
export function CardSprite() {
  return <div dangerouslySetInnerHTML={{ __html: spriteMarkup }} />;
}
