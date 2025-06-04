from pathlib import Path

def get_model_paths(user_id):
    """
    Returns the model paths for a given user.
    """
    base_dir = Path(__file__).resolve().parent.parent  # Regola in base alla struttura del tuo progetto
    models_dir = base_dir / "models"
    models_dir.mkdir(parents=True, exist_ok=True)  # Assicura che la directory esista

    model_cad_path = models_dir / f"model_cad_user_{user_id}.pkl"
    model_spd_path = models_dir / f"model_spd_user_{user_id}.pkl"

    return model_cad_path, model_spd_path
