# Day 5 LoRA Validation Summary

CLIP model: `openai/clip-vit-base-patch32`.

Reference CLIP similarity is the cosine similarity between each generated image and the mean CLIP image embedding of the 9 prepared earphone training photos, multiplied by 100. Higher is better.

| Method | Images | Avg time no-warmup (s) | Avg peak VRAM (GB) | Avg reference similarity | Avg prompt CLIPScore |
| --- | ---: | ---: | ---: | ---: | ---: |
| base | 6 | 0.884 | 6.979 | 80.680 | 32.681 |
| lora_scale_2 | 6 | 1.230 | 6.985 | 78.423 | 32.472 |

Interpretation: this metric is only a proxy for subject identity. It should be used together with the base-vs-LoRA visual grid, because CLIP image embeddings can miss fine-grained product details.
