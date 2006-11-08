<?php
class timereport extends atkNode
{
	function timereport()
	{
		$this->atkNode("timereport");
	}

	function action_search()
	{
		global $g_user, $g_db;

		$date = $this->m_postvars['date'];

		$sql = "SELECT id, activitydate, userid, phaseid, activityid, remark, time FROM hours WHERE activitydate = '$date' AND userid = " . $g_user["id"];
		$result = $g_db->getRows($sql);

		foreach ($result as $r)
		{
			foreach ($r as $item)
			{
				echo "$item\t";
			}
			echo "\n";
		}

		exit;
	}
}
?>
