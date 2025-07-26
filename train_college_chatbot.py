from datasets import load_dataset
from transformers import AutoTokenizer, AutoModelForSeq2SeqLM, Trainer, TrainingArguments, DataCollatorForSeq2Seq

# Load your custom dataset
dataset = load_dataset("json", data_files="college_faq.json")["train"]

# Format data
def format_data(example):
    example["input"] = f"### Question: {example['prompt']}"
    example["output"] = example["response"]
    return example

dataset = dataset.map(format_data)

# Use FLAN-T5 or switch to a different model
model_name = "google/flan-t5-small"  # This might work better
tokenizer = AutoTokenizer.from_pretrained(model_name)
model = AutoModelForSeq2SeqLM.from_pretrained(model_name)

# Tokenize
def tokenize(example):
    inputs = tokenizer(example["input"], padding="max_length", truncation=True, max_length=128)
    targets = tokenizer(example["output"], padding="max_length", truncation=True, max_length=128)
    inputs["labels"] = targets["input_ids"]
    return inputs

tokenized = dataset.map(tokenize)

# Set up training
training_args = TrainingArguments(
    output_dir="./t5-college-chatbot",
    per_device_train_batch_size=8,
    num_train_epochs=5,
    logging_steps=10,
    save_steps=500,
    save_total_limit=2,
    evaluation_strategy="no"
)

trainer = Trainer(
    model=model,
    args=training_args,
    train_dataset=tokenized,
    data_collator=DataCollatorForSeq2Seq(tokenizer, model)
)

# Train the model
trainer.train()

# Save the model
trainer.save_model("college-admission-chatbot")
tokenizer.save_pretrained("college-admission-chatbot")

print("Model training complete. Saved to ./college-admission-chatbot")
