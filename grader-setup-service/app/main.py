from flask import Flask
from flask import jsonify

from grader_service import GraderServiceLauncher


app = Flask(__name__)


@app.route("/<org_name>/<course_id>/launch")
def hello(org_name: str, course_id: str):
    launcher = GraderServiceLauncher(course_id=course_id)
    if not launcher.grader_deployment_exists():
        launcher.create_grader_deployment()
        return jsonify(success=True)
    else:
        return jsonify(success=True, message="A grader service already exists"), 409


@app.route("/healthcheck")
def healthcheck():
    return jsonify(success=True)


if __name__ == "__main__":
    app.run(host='0.0.0.0')