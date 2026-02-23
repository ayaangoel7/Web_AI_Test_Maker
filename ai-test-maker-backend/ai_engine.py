import torch  # type: ignore
from pathlib import Path

from transformers import (  # type: ignore
    AutoTokenizer,
    AutoModelForCausalLM,
    CLIPProcessor,
    CLIPModel,
    BitsAndBytesConfig,
)
from sentence_transformers import SentenceTransformer  # type: ignore
from huggingface_hub import snapshot_download  # type: ignore


class AIEngine:
    def __init__(self):
        # Store models in local app folder
        script_dir = Path(__file__).parent.absolute()
        self.model_dir = script_dir / "models"
        self.model_dir.mkdir(parents=True, exist_ok=True)

        self.device = "cuda" if torch.cuda.is_available() else "cpu"
        print(f"Device: {self.device}")
        if self.device == "cuda":
            total_memory = torch.cuda.get_device_properties(0).total_memory / 1e9
            print(f"Available VRAM: {total_memory:.2f} GB")

        # Base (unquantized) Phi-3 – we quantize at load time
        self.llm_name = "microsoft/Phi-3-mini-4k-instruct"
        self.embedding_name = "sentence-transformers/all-MiniLM-L6-v2"
        self.clip_name = "openai/clip-vit-base-patch32"

        # Model instances
        self.llm = None
        self.tokenizer = None
        self.embedding_model = None
        self.clip_model = None
        self.clip_processor = None

        # Load models if they exist
        if self.models_exist():
            self.load_models()

    def models_exist(self):
        """Check if models are downloaded"""
        llm_path = self.model_dir / "llm"
        embedding_path = self.model_dir / "embeddings"
        clip_path = self.model_dir / "clip"
        return (
            llm_path.exists()
            and embedding_path.exists()
            and clip_path.exists()
        )

    def download_models_safe(self, progress_callback):
        """Download all required models with SAFE callbacks for Tkinter threading"""
        print("Starting model downloads...")
        try:
            # Download LLM (base Phi-3)
            progress_callback(0.1, "Downloading LLM model...")
            llm_path = self.model_dir / "llm"
            if not llm_path.exists():
                print(f"Downloading LLM: {self.llm_name}")
                snapshot_download(
                    repo_id=self.llm_name,
                    local_dir=str(llm_path),
                    local_dir_use_symlinks=False,
                )

            # Download embedding model
            progress_callback(0.4, "Downloading embedding model...")
            embedding_path = self.model_dir / "embeddings"
            if not embedding_path.exists():
                print(f"Downloading embeddings: {self.embedding_name}")
                snapshot_download(
                    repo_id=self.embedding_name,
                    local_dir=str(embedding_path),
                    local_dir_use_symlinks=False,
                )

            # Download CLIP
            progress_callback(0.7, "Downloading CLIP model...")
            clip_path = self.model_dir / "clip"
            if not clip_path.exists():
                print(f"Downloading CLIP: {self.clip_name}")
                snapshot_download(
                    repo_id=self.clip_name,
                    local_dir=str(clip_path),
                    local_dir_use_symlinks=False,
                )

            # Load models
            progress_callback(0.95, "Loading models...")
            self.load_models()

            progress_callback(1.0, "Complete!")
            print("All models downloaded and loaded successfully!")

        except Exception as e:
            print(f"Error downloading models: {e}")
            progress_callback(1.0, f"Error: {str(e)}")

    def load_models(self):
        """Load models into memory (4-bit quantized)"""
        print("Loading models...")
        llm_path = self.model_dir / "llm"
        embedding_path = self.model_dir / "embeddings"
        clip_path = self.model_dir / "clip"

        try:
            # Tokenizer
            self.tokenizer = AutoTokenizer.from_pretrained(
                str(llm_path),
                local_files_only=True,
            )

            # 4-bit NF4 quantization config (BitsAndBytes)
            print("Loading Phi-3 in 4-bit NF4 with BitsAndBytes...")
            bnb_config = BitsAndBytesConfig(
                load_in_4bit=True,
                bnb_4bit_use_double_quant=True,
                bnb_4bit_quant_type="nf4",
                bnb_4bit_compute_dtype=torch.bfloat16,
            )

            self.llm = AutoModelForCausalLM.from_pretrained(
                str(llm_path),
                local_files_only=True,
                quantization_config=bnb_config,
                device_map="auto",
                low_cpu_mem_usage=True,
                trust_remote_code=False,
            )
            print(f"LLM dtype: {self.llm.dtype}")
            print(f"LLM device: {self.llm.device}")

            # Embedding model
            print("Loading embedding model...")
            self.embedding_model = SentenceTransformer(
                str(embedding_path),
                device=self.device,
            )

            # CLIP
            print("Loading CLIP model...")
            self.clip_processor = CLIPProcessor.from_pretrained(
                str(clip_path),
                local_files_only=True,
            )
            self.clip_model = CLIPModel.from_pretrained(
                str(clip_path),
                local_files_only=True,
            ).to(self.device)

            print("Models loaded successfully!")

        except Exception as e:
            print(f"Error loading models: {e}")
            raise

    def generate_text(self, prompt, max_tokens=1024, temperature=0.7):
        """Generate text using LLM"""
        if self.llm is None:
            raise RuntimeError("LLM not loaded")

        formatted_prompt = f"<|user|>\n{prompt}<|end|>\n<|assistant|>\n"

        inputs = self.tokenizer(
            formatted_prompt,
            return_tensors="pt",
            truncation=True,
            max_length=2048,
        ).to(self.device)

        with torch.no_grad():
            outputs = self.llm.generate(
                **inputs,
                max_new_tokens=max_tokens,
                temperature=temperature,
                do_sample=True,
                top_p=0.9,
                pad_token_id=self.tokenizer.eos_token_id,
            )

        response = self.tokenizer.decode(outputs[0], skip_special_tokens=True)
        if "<|assistant|>" in response:
            response = response.split("<|assistant|>")[-1].strip()

        # FIX: Explicitly clear GPU memory after generation to prevent crashes
        # on subsequent calls. This is crucial for stability in a server environment.
        del inputs
        del outputs
        if self.device == "cuda":
            torch.cuda.empty_cache()

        return response

    def get_embeddings(self, texts):
        """Get embeddings for text"""
        if self.embedding_model is None:
            raise RuntimeError("Embedding model not loaded")
        if isinstance(texts, str):
            texts = [texts]
        embeddings = self.embedding_model.encode(
            texts,
            convert_to_tensor=True,
            device=self.device,
        )
        return embeddings

    def get_image_embeddings(self, image_arrays):
        """Get CLIP embeddings for images"""
        if self.clip_model is None:
            raise RuntimeError("CLIP model not loaded")
        if not isinstance(image_arrays, list):
            image_arrays = [image_arrays]
        inputs = self.clip_processor(
            images=image_arrays,
            return_tensors="pt",
            padding=True,
        ).to(self.device)
        with torch.no_grad():
            embeddings = self.clip_model.get_image_features(**inputs)
        return embeddings

    def compute_similarity(self, emb1, emb2):
        """Compute cosine similarity between embeddings"""
        if isinstance(emb1, list):
            emb1 = torch.tensor(emb1)
        if isinstance(emb2, list):
            emb2 = torch.tensor(emb2)
        emb1 = emb1 / emb1.norm(dim=-1, keepdim=True)
        emb2 = emb2 / emb2.norm(dim=-1, keepdim=True)
        similarity = torch.sum(emb1 * emb2, dim=-1)
        if similarity.numel() == 1:
            return float(similarity.item())
        else:
            return float(similarity.mean().item())
