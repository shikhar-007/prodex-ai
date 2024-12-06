from django.shortcuts import render

# Create your views here.

from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
import json
from .utils import load_chromadb, create_retrieval_qa_chain

@csrf_exempt
def ask_question(request):
    if request.method == 'POST':
        try:
            # Parse the incoming request JSON data
            data = json.loads(request.body)
            question = data.get("question", "")

            # Check if the question is valid
            if not question:
                return JsonResponse({"error": "No question provided."}, status=400)

            # Load the ChromaDB vector store and create the QA chain
            vector_store = load_chromadb("db")
            if not vector_store:
                return JsonResponse({"error": "ChromaDB not found."}, status=500)

            qa_chain = create_retrieval_qa_chain(vector_store)
            answer = qa_chain(question)

            # Return the response as JSON
            return JsonResponse({"answer": answer})

        except Exception as e:
            return JsonResponse({"error": str(e)}, status=500)

    return JsonResponse({"error": "Invalid request method."}, status=405)