# Fine-tuning script for DistilBERT on toxic communication detection.
# Uses Jigsaw dataset + custom examples for our specific categories.
# Run once to train the model, then use it as gate in classifier.py

import json
from pathlib import Path
from datasets import load_dataset, Dataset
import pandas as pd
from transformers import (
    DistilBertTokenizerFast,
    DistilBertForSequenceClassification,
    TrainingArguments,
    Trainer
)
import torch
from sklearn.metrics import accuracy_score, precision_recall_fscore_support

# ── Config ──────────────────────────────────────────────────────────────────
MODEL_NAME = "distilbert-base-uncased"
OUTPUT_DIR = Path(__file__).parent.parent.parent.parent / "models" / "toxic_gate"
CUSTOM_EXAMPLES_PATH = Path(__file__).parent.parent.parent.parent / "data" / "custom_examples.json"

# ── Custom examples for categories not covered by Jigsaw ────────────────────
CUSTOM_EXAMPLES = [
    # Gaslighting
    {"text": "That never happened, you are imagining things.", "label": 1},
    {"text": "You are too sensitive, stop overreacting.", "label": 1},
    {"text": "I never said that. You must be confusing me with someone else.", "label": 1},
    {"text": "You always twist my words.", "label": 1},
    {"text": "You are crazy, that is not what happened.", "label": 1},
    {"text": "Nobody else has a problem with me, only you.", "label": 1},
    {"text": "You are remembering it wrong again.", "label": 1},
    {"text": "Stop making things up to make me look bad.", "label": 1},

    # Isolation
    {"text": "I do not want you spending time with them anymore.", "label": 1},
    {"text": "Your friends are a bad influence on you.", "label": 1},
    {"text": "If you really loved me you would not need to see other people.", "label": 1},
    {"text": "Your family does not understand us like I do.", "label": 1},
    {"text": "I am the only one who truly cares about you.", "label": 1},
    {"text": "Every time you see them you come back in a bad mood.", "label": 1},
    {"text": "Why do you need friends when you have me?", "label": 1},
    {"text": "I feel like you prefer them over me.", "label": 1},

    # Jealousy and control
    {"text": "Who were you texting just now?", "label": 1},
    {"text": "I need to know where you are at all times.", "label": 1},
    {"text": "Why did it take you so long to reply?", "label": 1},
    {"text": "I do not want you talking to him anymore.", "label": 1},
    {"text": "Send me your location right now.", "label": 1},
    {"text": "I checked your phone and I saw the messages.", "label": 1},
    {"text": "You are always flirting with other people.", "label": 1},
    {"text": "If you go out tonight do not bother coming back.", "label": 1},

    # Manipulation
    {"text": "After everything I have done for you, this is how you treat me?", "label": 1},
    {"text": "If you loved me you would do this for me.", "label": 1},
    {"text": "I guess I will just suffer alone then.", "label": 1},
    {"text": "Nobody else would put up with you like I do.", "label": 1},
    {"text": "You owe me after all I have sacrificed for you.", "label": 1},
    {"text": "I do everything for this family and nobody appreciates me.", "label": 1},
    {"text": "Fine, do whatever you want. I do not matter anyway.", "label": 1},
    {"text": "You always make me feel like the bad guy.", "label": 1},

    # Coercive control
    {"text": "You will do as I say or there will be consequences.", "label": 1},
    {"text": "I control the money in this house.", "label": 1},
    {"text": "You need my permission before you make any decisions.", "label": 1},
    {"text": "I decide what you wear and where you go.", "label": 1},
    {"text": "Without me you have nothing.", "label": 1},
    {"text": "I will make sure everyone knows what you did.", "label": 1},
    {"text": "You are not allowed to work, I take care of everything.", "label": 1},
    {"text": "If you leave I will take the children.", "label": 1},

    # Neutral examples to balance
    {"text": "Good morning! How are you today?", "label": 0},
    {"text": "Can we meet tomorrow at 10am?", "label": 0},
    {"text": "Thank you so much for your help yesterday.", "label": 0},
    {"text": "I really enjoyed our conversation.", "label": 0},
    {"text": "Could you send me the report when you get a chance?", "label": 0},
    {"text": "Happy birthday! Hope you have a wonderful day.", "label": 0},
    {"text": "I will be a few minutes late, sorry!", "label": 0},
    {"text": "Let me know if you need anything.", "label": 0},
    {"text": "The meeting has been moved to Thursday.", "label": 0},
    {"text": "I am proud of what we accomplished together.", "label": 0},
    {"text": "See you tomorrow!", "label": 0},
    {"text": "Can you pick up some milk on your way home?", "label": 0},
    {"text": "I disagree but I understand your point of view.", "label": 0},
    {"text": "Let us find a solution that works for both of us.", "label": 0},
    {"text": "I appreciate everything you do for me.", "label": 0},
    {"text": "How was your day?", "label": 0},
    {"text": "Hey! Are we still on for Saturday?", "label": 0},
    {"text": "Sorry I missed your call, been super busy lately!", "label": 0},
    {"text": "No worries, let us reschedule. How about next weekend?", "label": 0},
    {"text": "Miss hanging out with you!", "label": 0},
    {"text": "Happy to catch up whenever you are ready, no pressure!", "label": 0},
    {"text": "Had a great time today, thanks for being such a good friend!", "label": 0},
    {"text": "Can we talk when you have a moment?", "label": 0},
    {"text": "Thanks for being there for me!", "label": 0},
    {"text": "How are you doing lately?", "label": 0},
    {"text": "Just checking in, hope everything is okay!", "label": 0},
    {"text": "Are you free this weekend?", "label": 0},
    {"text": "Let me know if you need anything!", "label": 0},
    {"text": "I was wondering if we could catch up soon?", "label": 0},
    {"text": "Hope you have a great week!", "label": 0},
    {"text": "Did you get my message from earlier?", "label": 0},
    {"text": "I am running a bit late, be there in 10 minutes!", "label": 0},
    {"text": "Can we reschedule our meeting to Thursday?", "label": 0},
    {"text": "Just wanted to say hi and see how you are doing!", "label": 0},
    {"text": "It was so nice seeing you the other day!", "label": 0},
    {"text": "I noticed you seemed a bit quiet today, everything okay?", "label": 0},
    {"text": "You seem a bit off today, everything okay?", "label": 0},
    {"text": "I miss our chats, we should catch up soon!", "label": 0},
    {"text": "Sorry for the late reply, things have been hectic!", "label": 0},
    {"text": "Thanks for your help yesterday, really appreciated it!", "label": 0},
    {"text": "Looking forward to seeing you this weekend!", "label": 0},
    {"text": "I have been thinking about what you said and I think you are right.", "label": 0},
    {"text": "Can I ask you something? I need your advice.", "label": 0},
    {"text": "I hope things are better for you now.", "label": 0},
    {"text": "Thank you for always being so supportive!", "label": 0},
    {"text": "I feel like we have not talked in ages, how are you?", "label": 0},
    {"text": "I noticed you have been a bit distant lately. Miss hanging out!", "label": 0},
    {"text": "No rush, just let me know when you are ready.", "label": 0},
    {"text": "I am proud of you for what you accomplished!", "label": 0},
    {"text": "You did such a great job today!", "label": 0},
    {"text": "I was expecting your call but no worries, talk soon!", "label": 0},
    {"text": "Is everything okay? You seemed stressed earlier.", "label": 0},
    {"text": "I wish you had told me, I would have helped!", "label": 0},
    {"text": "I waited for you but no problem, we can reschedule.", "label": 0},
    {"text": "I felt a bit left out but I understand you were busy.", "label": 0},
    {"text": "I was a bit disappointed but I know things come up.", "label": 0},
    {"text": "I need some space to think, nothing personal.", "label": 0},
    {"text": "I have been feeling a bit overwhelmed lately.", "label": 0},
    {"text": "Can we talk about what happened yesterday?", "label": 0},
    {"text": "I felt hurt when you said that, can we discuss it?", "label": 0},
    {"text": "I understand if you are busy, just let me know!", "label": 0},
    {"text": "I disagreed with what you said but I respect your view.", "label": 0},
    {"text": "I would appreciate it if you could let me know next time.", "label": 0},
    {"text": "I feel better when we communicate openly like this.", "label": 0},
    {"text": "I appreciate you being honest with me.", "label": 0},
    {"text": "Let us find a solution that works for both of us.", "label": 0},
    {"text": "I have been meaning to call you, things have been crazy busy lately!", "label": 0},
    {"text": "Been swamped with work, sorry for the late reply!", "label": 0},
    {"text": "Things have been hectic but I have not forgotten about you!", "label": 0},
    {"text": "Sorry for going quiet, life has been a bit overwhelming lately.", "label": 0},
    {"text": "Just got your message, been a crazy week!", "label": 0},
    {"text": "Finally some free time, how have you been?", "label": 0},
    {"text": "Hey, just wanted to check if you got my message from earlier!", "label": 0},
    {"text": "Been meaning to reach out, hope you are doing well!", "label": 0},
    {"text": "Sorry I disappeared, work has been intense.", "label": 0},
    {"text": "Long time no talk! How are things going?", "label": 0},
]

def load_jigsaw(n_samples: int = 2000) -> pd.DataFrame:
    """Load a balanced sample from the civil_comments dataset."""
    print("Loading civil_comments dataset...")
    dataset = load_dataset("google/civil_comments", split="train")
    df = dataset.to_pandas()[["text", "toxicity"]]
    
    # Convert toxicity score to binary label
    df["label"] = (df["toxicity"] >= 0.5).astype(int)
    df = df[["text", "label"]]

    # Balance toxic and non-toxic
    toxic = df[df["label"] == 1].sample(n=n_samples // 2, random_state=3)
    non_toxic = df[df["label"] == 0].sample(n=n_samples // 2, random_state=3)
    balanced = pd.concat([toxic, non_toxic]).sample(frac=1, random_state=3)

    print(f"Civil comments samples: {len(balanced)}")
    return balanced

def compute_metrics(pred):
    labels = pred.label_ids
    preds = pred.predictions.argmax(-1)
    precision, recall, f1, _ = precision_recall_fscore_support(labels, preds, average="binary")
    acc = accuracy_score(labels, preds)
    return {"accuracy": acc, "f1": f1, "precision": precision, "recall": recall}

def load_daily_dialog(n_samples: int = 500) -> pd.DataFrame:
    """Load neutral and happy utterances from better_daily_dialog as non-toxic examples."""
    print("Loading daily dialog dataset...")
    dataset = load_dataset("pixelsandpointers/better_daily_dialog", split="train")
    df = dataset.to_pandas()
    
    # Keep only neutral (0) and happy (3) emotions
    neutral = df[df["emotion"].isin([0, 3])][["utterance"]].copy()
    neutral = neutral.rename(columns={"utterance": "text"})
    neutral["label"] = 0
    
    # Sample
    sampled = neutral.sample(n=min(n_samples, len(neutral)), random_state=3)
    print(f"Daily dialog samples: {len(sampled)}")
    return sampled


def finetune():
    # Load and merge datasets
    jigsaw_df = load_jigsaw(n_samples=2000)
    daily_df = load_daily_dialog(n_samples=500)
    custom_df = pd.DataFrame(CUSTOM_EXAMPLES)
    
    df = pd.concat([jigsaw_df, daily_df, custom_df]).sample(frac=1, random_state=3).reset_index(drop=True)
    print(f"Total training samples: {len(df)}")

    # Split train/eval
    split = int(len(df) * 0.85)
    train_df = df[:split]
    eval_df = df[split:]

    # Tokenise
    tokenizer = DistilBertTokenizerFast.from_pretrained(MODEL_NAME)

    def tokenize(batch):
        return tokenizer(batch["text"], truncation=True, padding=True, max_length=128)

    train_dataset = Dataset.from_pandas(train_df[["text", "label"]])
    eval_dataset = Dataset.from_pandas(eval_df[["text", "label"]])

    train_dataset = train_dataset.map(tokenize, batched=True)
    eval_dataset = eval_dataset.map(tokenize, batched=True)

    train_dataset = train_dataset.rename_column("label", "labels")
    eval_dataset = eval_dataset.rename_column("label", "labels")
    train_dataset.set_format("torch", columns=["input_ids", "attention_mask", "labels"])
    eval_dataset.set_format("torch", columns=["input_ids", "attention_mask", "labels"])

    # Model
    model = DistilBertForSequenceClassification.from_pretrained(MODEL_NAME, num_labels=2)

    # Training args
    training_args = TrainingArguments(
        output_dir=str(OUTPUT_DIR),
        num_train_epochs=3,
        per_device_train_batch_size=16,
        per_device_eval_batch_size=16,
        eval_strategy="epoch",
        save_strategy="epoch",
        load_best_model_at_end=True,
        metric_for_best_model="f1",
        logging_dir=str(OUTPUT_DIR / "logs"),
        logging_steps=50,
    )

    trainer = Trainer(
        model=model,
        args=training_args,
        train_dataset=train_dataset,
        eval_dataset=eval_dataset,
        compute_metrics=compute_metrics,
    )

    print("Starting fine-tuning...")
    trainer.train()

    # Save model
    trainer.save_model(str(OUTPUT_DIR))
    tokenizer.save_pretrained(str(OUTPUT_DIR))
    print(f"Model saved to {OUTPUT_DIR}")

if __name__ == "__main__":
    finetune()