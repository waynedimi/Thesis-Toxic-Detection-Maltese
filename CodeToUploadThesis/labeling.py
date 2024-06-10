# Function to classify a comment as toxic or non-toxic
def classify_comment(comment):
    response = client.chat.completions.create(
        model="gpt-4o",
        messages=[
            {"role": "system", "content": "You are a helpful assistant that classifies comments as toxic or non-toxic in Maltese and provides a reason for the classification. Follow this structure in your response:\n\ncomments: <original comment>\nreason: <reason for classification>\nisToxic: <1 for toxic, 0 for non-toxic>"},
            {"role": "user", "content": f"Classify the following comment as toxic or non-toxic, and provide a reason: {comment}"}
        ],
        max_tokens=2000,
        temperature=0.5,
    )
    classification_response = response.choices[0].message.content.strip().split('\n')
    comment_text = classification_response[0].replace('comments: ', '').strip()
    reason = classification_response[1].replace('reason: ', '').strip() if len(classification_response) > 1 else ""
    is_toxic = 1 if 'isToxic: 1' in classification_response[-1] else 0
    return comment_text, reason, is_toxic