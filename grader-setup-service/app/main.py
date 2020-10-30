from flask import Flask
from flask import jsonify

from . import create_app
from .models import db
from .models import GraderService
from .grader_service import GraderServiceLauncher


app = create_app()


@app.route('/services/<org_name>/<course_id>', methods=['POST'])
def launch(org_name: str, course_id: str):
    """
    Creates a new grader-notebook pod if not exists
    """
    launcher = GraderServiceLauncher(org_name=org_name, course_id=course_id)
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
        return jsonify(success=False, message=f'A grader service already exists for this course_id:{course_id}'), 409


@app.route('/services', methods=['GET'])
def services():
    """
    Returns the grader-notebook list used as services in jhub

    Response: json
    example:
    ```
    {
        services: [{"name":"<course-id", "url": "http://grader-<course-id>:8888"...}],
        groups: {"formgrade-<course-id>": ["grader-<course-id>"] }
    }
    ```
    """
    services = GraderService.query.all()
    # format a json
    services_resp = []
    groups_resp = {}
    for s in services:
        services_resp.append({
            'name': s.name,
            'url': s.url,
            'oauth_no_confirm': s.oauth_no_confirm,
            'admin': s.admin,
            'api_token': s.api_token
        })
        # add the jhub user group
        groups_resp.update({f'formgrade-{s.course_id}': [f'grader-{s.course_id}']})
    return jsonify(services=services_resp, groups=groups_resp)


@app.route("/services/<org_name>/<course_id>", methods=['DELETE'])
def services_deletion(org_name: str, course_id: str):
    launcher = GraderServiceLauncher(org_name=org_name, course_id=course_id)
    try:
        launcher.delete_grader_deployment()
        service_saved = GraderService.query.filter_by(course_id=course_id).first()
        if service_saved:
            db.session.delete(service_saved)
            db.session.commit()
        return jsonify(success=True)
    except Exception as e:
        return jsonify(success=False, error=str(e)), 500


@app.route("/healthcheck")
def healthcheck():
    return jsonify(success=True)


if __name__ == "__main__":
    app.run(host='0.0.0.0')
