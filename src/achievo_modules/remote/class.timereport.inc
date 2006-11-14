<?php
include_once (moduleDir("remote")."class.timereg.inc");

class timereport extends atkNode
{
	function timereport()
	{
		$this->atkNode("timereport");
		$this->setSecurityAlias("remote.timereg");
	}

	function action_search()
	{
		atkdebug("timereport Action search");
		global $g_user;

		$db = &atkGetDb();
		$date = $this->m_postvars['date'];
		// faccio un controllo per far passare solo le date
		// nel formato YYYY-[M]M-[D]D
		if (!is_array($date))
			$date = array($date);
		$date = array_filter($date, is_valid_date);
		$datelist = implode("','", $date);
		
		$sql = "
			SELECT id, activitydate, userid, phaseid, activityid, remark, time
			FROM hours WHERE activitydate IN ('$datelist',0)
			AND userid = " . $g_user["id"] . " ORDER BY activitydate DESC
		";
		$results = $db->getRows($sql);

		echo make_xml("OK", $results);
		exit;
	}
}
?>
