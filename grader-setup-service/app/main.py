from flask import Flask
from flask import jsonify

from . import create_app
from .models import db
from .models import GraderService
from .grader_service import GraderServiceLauncher


app = create_app()


@app.route("/<org_name>/<course_id>/launch")
def launch(org_name: str, course_id: str):
    launcher = GraderServiceLauncher(course_id=course_id)
    if not launcher.grader_deployment_exists():
        launcher.create_grader_deployment()
        new_service = GraderService(
            name=course_id,
            course_id=course_id,
            url=f'http://{launcher.grader_name}:8888',
            api_token=launcher.grader_token
        )
        db.session.add(new_service)
        db.session.commit()

        return jsonify(success=True)
    else:
        return jsonify(success=False, message="A grader service already exists"), 409


@app.route("/services", methods=["GET"])
def services():
    services = GraderService.query.all()
    return jsonify(services)


@app.route("/healthcheck")
def healthcheck():
    return jsonify(success=True)


if __name__ == "__main__":
    app.run(host='0.0.0.0')
