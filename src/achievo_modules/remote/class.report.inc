<?php
/*
 * Copyright 2007 Develer S.r.l. (http://www.develer.com/)
 * All rights reserved.
 *
 * $Id: $
 * Author: Matteo Bertini <naufraghi@develer.com>
 */

include_once (moduleDir("remote")."class.timereg.inc");

class report extends atkNode
{
    function report()
    {
        $this->atkNode("report");
        $this->setSecurityAlias("remote.timereg");
    }

    function action_search()
    {
        global $g_user;

        $db = &atkGetDb();
		if(!isset($this->m_postvars["projectid"])) {
			$sql = "SELECT project.id, project.name FROM project JOIN project_person ON project.id = project_person.projectid WHERE project_person.personid = {$g_user["id"]}";
			$results = $db->getRows($sql);
			echo make_xml("project", "OK", $results);
			exit;
		} else {
			$projectid = $this->m_postvars["projectid"];
			$sql = "select hours.activitydate as date, hours.time, hours.remark, activity.name as activity, phase.name as phase, person.userid as user
				from hours
				join
				phase on hours.phaseid = phase.id
				join
				project on phase.projectid = project.id
				join
				activity on hours.activityid = activity.id
				join
				person
				on hours.userid = person.id
				where
				project.id = $projectid";
			if(isset($this->m_postvars["from_date"])) {
				$from_date = $this->m_postvars["from_date"];
				$sql .= " and hours.activitydate >= '$from_date'";
			}
			if(isset($this->m_postvars["to_date"])) {
				$to_date = $this->m_postvars["to_date"];
				$sql .= " and hours.activitydate <= '$to_date'";
			}
			$sql .= " order by date";
			$result = $db->getRows($sql);
			echo make_xml("hours", "OK", $result);
			exit;
		}
    }
}
?>
