# Copyright 2024 Google. All Rights Reserved.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
import config
import argparse

from google.cloud import aiplatform
import google.cloud.logging

import gradio as gr

parser = argparse.ArgumentParser()
parser.add_argument(
    "--project-id",
    type=str,
    default=None,
    help="GCP project hosts the custom model."
)
parser.add_argument(
    "--location",
    type=str,
    default=None,
    help="location of the custom model."
)
parser.add_argument(
    "--endpoint",
    type=str,
    default=None,
    help="Vertex AI endpoint where the custom model is deployed."
)

args = parser.parse_args()


client = google.cloud.logging.Client(project=args.project_id)
client.setup_logging()

log_name = "test-llm"
logger = client.logger(log_name)

aiplatform.init(project=args.project_id, location=args.location)
endpoint = aiplatform.Endpoint(args.endpoint)

def predict(prompt):
  logger.log_text(prompt)
  instances = [
      {
          "prompt": prompt
      }
  ]
  answer = endpoint.predict(instances=instances)

  return answer.predictions[0]["content"]


gr.close_all()
demo = gr.Interface(
    fn=predict,
    inputs=[gr.Textbox(label="Input", lines=6)],
    outputs=[gr.Textbox(label="Output", lines=6)],
    title="Prediction From Custom Trained Model",
    examples=config.EXAMPLES,
)
demo.launch(share=False, server_port=7860, server_name="0.0.0.0")
