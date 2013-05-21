function error_message(msg) {
    d3.select(document.body)
        .append("h1")
        .style("color", "red")
        .text(msg);
}

function servicePath(){
    var pathArgs = Array.slice(arguments).join("/");
    if (pathArgs.length > 0) {
        pathArgs = "/" + pathArgs;
    }

    return "../tangelo/projmgr" + pathArgs;
}

window.onload = function () {
    "use strict";

    var hl_proj = null,
        hl_type = null,
        hl_dataset = null;

    function refreshProjects(fade){
        var ajax,
            items,
            fresh;

        ajax = d3.json(servicePath("project"));
        ajax.send("GET", function (e, projects) {
            if (e) {
                error_message("Error!");
                console.log(e);
            }

            items = d3.select("#projects")
                .selectAll("div")
                .data(projects, function (d) {
                    return d;
                });

            fresh = items.enter()
                .append("div")
                .classed("item", true)
                .attr("name", function (d) {
                    return d;
                })
                .text(function (d) {
                    return d;
                })
                .on("click", function (d) {
                    // Move the highlight to the selected project (or remove the
                    // highlight entirely if the selected item is clicked
                    // again).
                    if (hl_proj !== null) {
                        d3.select("#projects")
                            .select("[name=" + hl_proj + "]")
                            .classed("selected", false);
                    }

                    if (hl_proj !== d) {
                        hl_proj = d;
                        d3.select(this)
                            .classed("selected", true);
                    } else {
                        hl_proj = null;
                    }

                    hl_type = null;
                    hl_dataset = null;

                    // Refresh the data type list.
                    if (hl_proj !== null) {
                        refreshDatatypes(hl_proj);
                    } else {
                        clearDatatypes();
                    }

                    // Clear the data set list.
                    clearDatasets();
                });

            fresh.append("a")
                .classed("btn", true)
                .classed("btn-mini", true)
                .text("delete")
                .on("click", function () {
                    deleteProject(d3.select(this.parentNode).attr("name"));
                });

            if (fade) {
                items.exit()
                    .transition()
                    .duration(1000)
                    .style("height", "0px")
                    .style("opacity", 0.0)
                    .remove();
            } else {
                items.exit()
                    .remove();
            }

            if (hl_proj !== null) {
                refreshDatatypes(hl_proj, fade);
            } else {
                hl_type = null;
                hl_dataset = null;
            }
        });
    }

    function deleteProject(project) {
        var ajax;

        ajax = d3.xhr(servicePath("project", project));
        ajax.send("DELETE", function (e, r) {
            if (e) {
                error_message("Error!");
                console.log(e);
                return;
            }

            hl_proj = null;
            refreshProjects(true);
        });
    }

    function refreshDatatypes(project, fade) {
        var ajax,
            items;

        ajax = d3.json(servicePath("project", project));
        ajax.send("GET", function (e, datatypes) {
            if (e) {
                error_message("Error!");
                console.log(e);
                return;
            }

            items = d3.select("#datatypes")
                .selectAll("div")
                .data(datatypes, function (d) {
                    return d;
                });

            items.enter()
                .append("div")
                .classed("item", true)
                .attr("name", function (d) {
                    return d;
                })
                .text(function (d) {
                    return d;
                })
                .on("click", function (d) {
                    // Move the highlight to the selected datatype (or remove
                    // the highlight entirely if the selected item is clicked
                    // again).
                    if (hl_type !== null) {
                        d3.select("#datatypes")
                            .select("[name=" + hl_type + "]")
                            .classed("selected", false);
                    }
                    if (hl_type !== d) {
                        hl_type = d;
                        d3.select(this)
                            .classed("selected", true);
                    } else {
                        hl_type = null;
                    }

                    hl_dataset = null;

                    // Refresh the data set list.
                    if (hl_type !== null) {
                        refreshDatasets(hl_proj, hl_type);
                    } else {
                        clearDatasets();
                    }
                });

            if (fade) {
                items.exit()
                    .transition()
                    .duration(1000)
                    .style("height", "0px")
                    .style("opacity", 0.0)
                    .remove();
            } else {
                items.exit()
                    .remove();
            }

            if (hl_type !== null) {
                refreshDatasets(hl_proj, hl_type, fade);
            } else {
                hl_dataset = null;
            }
        });
    }

    function refreshDatasets(project, type, fade) {
        var ajax;

        ajax = d3.json(servicePath("project", project, type));
        ajax.send("GET", function (e, datasets) {
            var items,
                fresh;

            if (e) {
                error_message("Error!");
                console.log(e);
                return;
            }

            items = d3.select("#datasets")
                .selectAll("div")
                .data(datasets, function (d) {
                    return d;
                });

            fresh = items.enter()
                .append("div")
                .classed("item", true)
                .attr("name", function (d) {
                    return d;
                })
                .text(function (d) {
                    return d;
                })
                .on("click", function (d) {
                    // Move the highlight to the selected dataset (or remove the
                    // highlight entirely if the selected item is clicked
                    // again).
                    if (hl_dataset !== null) {
                        d3.select("#datasets")
                            .select("[name=" + hl_dataset + "]")
                            .classed("selected", false);
                    }
                    if (hl_dataset !== d) {
                        hl_dataset = d;
                        d3.select(this)
                            .classed("selected", true);
                    } else {
                        hl_dataset = null;
                    }
                });

            fresh.append("a")
                .classed("btn", true)
                .classed("btn-mini", true)
                .text("delete")
                .on("click", function () {
                    deleteDataset(hl_proj, hl_type, d3.select(this.parentNode).attr("name"));
                });

            fresh.append("a")
                .classed("btn", true)
                .classed("btn-mini", true)
                .text("preview");

            fresh.append("a")
                .classed("btn", true)
                .classed("btn-mini", true)
                .text("select");

            if (fade) {
                items.exit()
                    .transition()
                    .duration(1000)
                    .style("height", "0px")
                    .style("opacity", 0.0)
                    .remove();
            } else {
                items.exit()
                    .remove();
            }
        });
    }

    function deleteDataset(project, type, dataset) {
        var ajax;

        ajax = d3.xhr(servicePath("project", project, type, dataset));
        ajax.send("DELETE", function (e, r) {
            if (e) {
                error_message("Error!");
                console.log(e);
                return;
            }

            hl_dataset = null;
            refreshDatasets(hl_proj, hl_type, true);
        });
    }

    function clearDatasets() {
        d3.select("#datasets")
            .selectAll("*")
            .remove();

        hl_dataset = null;
    }

    function clearDatatypes() {
        d3.select("#datatypes")
            .selectAll("*")
            .remove();

        hl_type = null;
    }


    d3.select("#newproject-ok")
        .on("click", function () {
            var name,
                ajax;

            name = encodeURI(d3.select("#newproject-name").property("value"));

            if (name !== "") {
                ajax = d3.xhr(servicePath("project", name));
                ajax.send("PUT", function (err, response) {
                    if (err) {
                        console.log("error: ");
                        console.log(err);
                        return;
                    }

                    refreshProjects(true);
                });
            }
        });

    refreshProjects(false);
};
