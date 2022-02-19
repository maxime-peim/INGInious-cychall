function load_input_cychall(submissionid, key, input) {
    var field = $("form#task input[name='" + key + "']");
    if(key in input)
        $(field).prop('value', input[key]);
    else
        $(field).prop('value', "");
}

function studio_init_template_cychall(well, pid, problem)
{ 
    if("exercice" in problem)
        $('#exercice-' + pid, well).val(problem["exercice"]).change();

    if("difficulty" in problem)
        $('#difficulty-' + pid, well).val(problem["difficulty"]).change();
}

function load_feedback_cychall(key, content) {
    load_feedback_code(key, content);
}