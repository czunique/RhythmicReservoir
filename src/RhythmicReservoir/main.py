"""Main entry point for the rhythmic-reservoir simulation workflow."""
from scripts.interactive_conceptual_model import render_interactive_conceptual_model


def main():
    print("Stage 1/1: opening the interactive 3D conceptual reservoir model...")
    output = render_interactive_conceptual_model(show=True)
    print(f"Interactive figure saved to: {output}")


if __name__ == "__main__":
    main()
